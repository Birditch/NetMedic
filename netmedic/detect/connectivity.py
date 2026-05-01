"""Connectivity / packet-loss checks via the system ``ping`` command.

We shell out to ``ping`` instead of using raw sockets so the tool runs without
admin privileges. Output is parsed with a regex that works against both English
and Chinese Windows locales (matching ``time=`` and ``时间=``).
"""
from __future__ import annotations
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class PingResult:
    host: str
    label: str
    sent: int
    received: int
    loss_pct: float
    avg_ms: float | None
    min_ms: int | None
    max_ms: int | None
    error: str | None = None


_TIME_RE = re.compile(r"(?:time|时间)[=<]\s*(\d+)\s*ms", re.IGNORECASE)


def ping(host: str, label: str = "", count: int = 4, timeout_ms: int = 1500) -> PingResult:
    label = label or host
    overall_timeout = (count * (timeout_ms / 1000.0)) + 4.0
    try:
        proc = subprocess.run(
            ["ping", "-n", str(count), "-w", str(timeout_ms), host],
            capture_output=True,
            timeout=overall_timeout,
        )
    except subprocess.TimeoutExpired:
        return PingResult(host, label, count, 0, 100.0, None, None, None, "timeout")
    except FileNotFoundError:
        return PingResult(host, label, count, 0, 100.0, None, None, None, "ping not found")

    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
    times = [int(m) for m in _TIME_RE.findall(out)]
    received = len(times)
    loss = (count - received) / count * 100.0
    if times:
        return PingResult(
            host, label, count, received, loss,
            avg_ms=sum(times) / len(times),
            min_ms=min(times),
            max_ms=max(times),
        )
    return PingResult(host, label, count, 0, 100.0, None, None, None, "no-reply")


def ping_many(targets: list[tuple[str, str]], count: int = 4) -> list[PingResult]:
    if not targets:
        return []
    with ThreadPoolExecutor(max_workers=min(8, len(targets))) as ex:
        return list(ex.map(lambda t: ping(t[0], t[1], count=count), targets))
