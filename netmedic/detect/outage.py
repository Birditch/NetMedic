"""End-to-end outage diagnosis: figure out *where* the network is broken.

Probes in order, stopping at the first failure:

1. Loopback: 127.0.0.1 reachable.
2. Default gateway: ARP / ping.
3. Internet IP: ping 1.1.1.1 (no DNS needed).
4. DNS resolution: resolve cloudflare.com via current DNS.
5. HTTP fetch: open https://1.1.1.1/cdn-cgi/trace.
"""
from __future__ import annotations
from dataclasses import dataclass

import socket
import subprocess

from ..utils import run_powershell


@dataclass
class OutageStep:
    name: str
    ok: bool
    detail: str


@dataclass
class OutageReport:
    steps: list[OutageStep]
    failing_step: int | None  # 1-indexed, None if everything passed
    summary: str
    fix_hint: str


def _ping(host: str, timeout_ms: int = 1000) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            capture_output=True, timeout=(timeout_ms / 1000) + 2,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "ping process failed"
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    if "TTL=" in out or "ttl=" in out:
        return True, out.split("\n")[1].strip() if "\n" in out else out
    return False, "no reply"


def _gateway() -> str | None:
    rc, out, _ = run_powershell(
        "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | "
        "Sort-Object RouteMetric, ifMetric | Select-Object -First 1).NextHop"
    )
    if rc != 0:
        return None
    line = out.strip().splitlines()[-1] if out.strip() else ""
    return line if line and line not in {"0.0.0.0", "::"} else None


def _resolve(domain: str = "cloudflare.com", timeout: float = 3.0) -> tuple[bool, str]:
    socket.setdefaulttimeout(timeout)
    try:
        ip = socket.gethostbyname(domain)
        return True, f"{domain} -> {ip}"
    except (socket.gaierror, OSError) as e:
        return False, str(e)
    finally:
        socket.setdefaulttimeout(None)


def _http_fetch(url: str = "https://1.1.1.1/cdn-cgi/trace", timeout: float = 5.0) -> tuple[bool, str]:
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read(512).decode("utf-8", errors="replace")
        return True, data.splitlines()[0] if data else "200 OK"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def diagnose() -> OutageReport:
    steps: list[OutageStep] = []

    # 1. Loopback
    ok, det = _ping("127.0.0.1", timeout_ms=500)
    steps.append(OutageStep("Loopback (127.0.0.1)", ok, det))

    # 2. Gateway
    gw = _gateway()
    if gw is None:
        steps.append(OutageStep("Default gateway", False, "no default route configured"))
    else:
        ok, det = _ping(gw)
        steps.append(OutageStep(f"Default gateway ({gw})", ok, det))

    # 3. Internet IP (no DNS)
    ok, det = _ping("1.1.1.1", timeout_ms=2000)
    steps.append(OutageStep("Internet (1.1.1.1)", ok, det))

    # 4. DNS resolve
    ok, det = _resolve()
    steps.append(OutageStep("DNS resolution", ok, det))

    # 5. HTTPS fetch
    ok, det = _http_fetch()
    steps.append(OutageStep("HTTPS fetch", ok, det))

    failing = next((i + 1 for i, s in enumerate(steps) if not s.ok), None)

    if failing is None:
        return OutageReport(steps, None,
                            "all checks passed",
                            "no action needed")

    fix_map = {
        1: ("loopback failed — kernel TCP/IP stack issue",
            "run `netsh int ip reset` then reboot"),
        2: ("gateway unreachable — local network / cable / Wi-Fi",
            "check cable / Wi-Fi password / IP setting; "
            "try `ipconfig /release` then `ipconfig /renew`"),
        3: ("gateway up but Internet unreachable — ISP / soft-router upstream",
            "check soft router, modem, or call ISP. Try plugging PC "
            "directly into the modem"),
        4: ("Internet up but DNS broken — DNS server misconfigured/poisoned",
            "run `python run.py force-doh` to switch to encrypted DNS"),
        5: ("DNS resolves but HTTPS fails — cert store / firewall / MITM",
            "check date/time, antivirus HTTPS scanning, "
            "or proxy settings"),
    }
    summary, hint = fix_map[failing]
    return OutageReport(steps, failing, summary, hint)
