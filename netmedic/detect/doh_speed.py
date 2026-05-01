"""Benchmark DoH endpoints by sending real DoH queries over HTTPS.

Critical: this is the *only* honest way to time DoH. Measuring plain UDP/53
to the same IPs gives garbage when a soft router intercepts port 53 — the
'1.1.1.1' you measured was the local cache, not Cloudflare.

The numbers we get here include TLS handshake, so cold queries are 2-3x
slower than what Windows actually pays once the connection is reused.
We still pick by these numbers because:
  1. Relative ranking between providers is preserved.
  2. The user's first hit per site pays exactly this cost; warm reuse is
     a bonus, not the baseline.
"""
from __future__ import annotations
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import dns.exception
import dns.message
import dns.query
import dns.rdatatype

from ..config import KNOWN_POISON_IPS, POLLUTION_TEST_DOMAINS


_TEST_DOMAINS = ("qq.com", "google.com", "github.com")


@dataclass
class DohResult:
    name: str
    url: str
    region: str
    operator: str
    notes: str
    v4_ips: list[str]
    v6_ips: list[str]
    avg_ms: float | None
    median_ms: float | None
    min_ms: float | None
    success_rate: float
    samples: int
    failures: int = 0
    polluted_domains: list[str] | None = None
    pollution_failed: bool = False

    @property
    def is_clean(self) -> bool:
        return self.polluted_domains == []  # explicit empty (not None)


def _measure_one(url: str, domain: str, timeout: float = 5.0) -> float | None:
    q = dns.message.make_query(domain, dns.rdatatype.A)
    start = time.perf_counter()
    try:
        dns.query.https(q, url, timeout=timeout)
    except (dns.exception.Timeout, dns.exception.DNSException, OSError, Exception):
        return None
    return (time.perf_counter() - start) * 1000.0


def _check_pollution_doh(url: str) -> tuple[list[str] | None, bool]:
    """Resolve sensitive domains via DoH; return (polluted_domain_list, failed).

    DoH responses can't be GFW-injected mid-flight (TLS), so the only way a
    domain ends up "polluted" here is if the upstream resolver itself is
    serving bogus answers from the GFW poison-IP set.
    """
    polluted: list[str] = []
    any_success = False
    for d in POLLUTION_TEST_DOMAINS:
        q = dns.message.make_query(d, dns.rdatatype.A)
        try:
            r = dns.query.https(q, url, timeout=5.0)
        except (dns.exception.Timeout, dns.exception.DNSException, OSError, Exception):
            continue
        any_success = True
        ips: list[str] = []
        for rrset in r.answer:
            for item in rrset:
                if item.rdtype == dns.rdatatype.A:
                    ips.append(item.to_text())
        if any(ip in KNOWN_POISON_IPS for ip in ips):
            polluted.append(d)
    if not any_success:
        return None, True
    return polluted, False


def benchmark_doh_provider(name: str, info: dict) -> DohResult:
    timings: list[float] = []
    failures = 0
    for d in _TEST_DOMAINS:
        t = _measure_one(info["url"], d)
        if t is None:
            failures += 1
        else:
            timings.append(t)
    samples = len(_TEST_DOMAINS)

    polluted, pollution_failed = _check_pollution_doh(info["url"])

    base = dict(
        name=name, url=info["url"], region=info["region"],
        operator=info.get("operator", ""), notes=info.get("notes", ""),
        v4_ips=info.get("v4_ips", []), v6_ips=info.get("v6_ips", []),
        samples=samples, failures=failures,
        polluted_domains=polluted, pollution_failed=pollution_failed,
    )
    if timings:
        return DohResult(
            avg_ms=statistics.mean(timings),
            median_ms=statistics.median(timings),
            min_ms=min(timings),
            success_rate=len(timings) / samples,
            **base,
        )
    return DohResult(
        avg_ms=None, median_ms=None, min_ms=None,
        success_rate=0.0,
        **base,
    )


def benchmark_all_doh(providers: dict) -> list[DohResult]:
    if not providers:
        return []
    workers = min(8, len(providers))
    items = list(providers.items())
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda kv: benchmark_doh_provider(kv[0], kv[1]), items))
