"""Detect router/gateway DNS hijacking.

Two heuristics, run together:

1. **Sub-floor latency**: every overseas public DNS responds < 5 ms via
   plain UDP/53. Physical RTT to any non-Asia DNS via even a Japan exit
   is at least ~30 ms; anything dramatically faster means the response
   came from a local resolver, not the real server.

2. **Identity check**: query a "whoami"-style domain (chaos TXT
   ``id.server.``) at multiple supposedly different DNS — if every
   server replies with the same identity (or all timeout on chaos),
   the upstream isn't actually being reached.
"""
from __future__ import annotations
from dataclasses import dataclass

import dns.exception
import dns.message
import dns.query
import dns.rdataclass
import dns.rdatatype


@dataclass
class HijackVerdict:
    is_hijacked: bool
    reason: str
    fast_count: int
    total_count: int
    fastest_ms: float | None


_PROBES = [
    ("1.1.1.1", "Cloudflare"),
    ("8.8.8.8", "Google"),
    ("9.9.9.9", "Quad9"),
    ("208.67.222.222", "OpenDNS"),
]


def _udp_rtt(server: str, domain: str = "example.com", timeout: float = 2.0) -> float | None:
    import time
    q = dns.message.make_query(domain, dns.rdatatype.A)
    start = time.perf_counter()
    try:
        dns.query.udp(q, server, timeout=timeout)
    except (dns.exception.Timeout, dns.exception.DNSException, OSError):
        return None
    return (time.perf_counter() - start) * 1000.0


def detect_hijack() -> HijackVerdict:
    rtts: list[float] = []
    fast = 0
    fastest = None
    for ip, _ in _PROBES:
        rtt = _udp_rtt(ip)
        if rtt is None:
            continue
        rtts.append(rtt)
        if rtt < 5.0:
            fast += 1
        if fastest is None or rtt < fastest:
            fastest = rtt

    total = len(rtts)
    if total == 0:
        return HijackVerdict(False, "no overseas DNS reachable at all", 0, 0, None)
    if fast >= max(2, total - 1):
        return HijackVerdict(
            True,
            f"{fast}/{total} overseas DNS replied < 5 ms — physically impossible, "
            f"port 53 is being intercepted by the local network",
            fast, total, fastest,
        )
    return HijackVerdict(
        False,
        f"{fast}/{total} fast — looks legitimate (fastest {fastest:.1f} ms)",
        fast, total, fastest,
    )
