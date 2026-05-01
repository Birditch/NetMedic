"""Benchmark DNS resolvers by latency and success rate."""
from __future__ import annotations
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import dns.exception
import dns.message
import dns.query
import dns.rdatatype

from ..config import (
    DNS_BENCH_WORKERS,
    DNS_QUERY_REPEAT,
    DNS_QUERY_TIMEOUT,
    SPEED_TEST_DOMAINS,
)
from ..data.public_dns import DnsServer


@dataclass
class DnsServerResult:
    server: DnsServer
    avg_ms: float | None
    median_ms: float | None
    success_rate: float
    samples: int
    failures: int = 0
    notes: str = ""


def _measure_one(ip: str, domain: str, timeout: float) -> float | None:
    q = dns.message.make_query(domain, dns.rdatatype.A)
    start = time.perf_counter()
    try:
        dns.query.udp(q, ip, timeout=timeout)
    except (dns.exception.Timeout, dns.exception.DNSException, OSError):
        return None
    return (time.perf_counter() - start) * 1000.0


def benchmark_server(
    server: DnsServer,
    domains: list[str] | None = None,
    repeat: int = DNS_QUERY_REPEAT,
    timeout: float = DNS_QUERY_TIMEOUT,
) -> DnsServerResult:
    domains = domains or SPEED_TEST_DOMAINS
    samples = 0
    failures = 0
    timings: list[float] = []
    for d in domains:
        for _ in range(repeat):
            samples += 1
            r = _measure_one(server.primary, d, timeout)
            if r is None:
                failures += 1
            else:
                timings.append(r)
    if timings:
        return DnsServerResult(
            server=server,
            avg_ms=statistics.mean(timings),
            median_ms=statistics.median(timings),
            success_rate=(samples - failures) / samples if samples else 0.0,
            samples=samples,
            failures=failures,
        )
    return DnsServerResult(
        server=server,
        avg_ms=None,
        median_ms=None,
        success_rate=0.0,
        samples=samples,
        failures=failures,
        notes="所有查询超时/失败",
    )


def benchmark_all(
    servers: list[DnsServer],
    domains: list[str] | None = None,
    repeat: int = DNS_QUERY_REPEAT,
) -> list[DnsServerResult]:
    if not servers:
        return []
    workers = min(DNS_BENCH_WORKERS, len(servers))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(
            lambda s: benchmark_server(s, domains=domains, repeat=repeat),
            servers,
        ))
