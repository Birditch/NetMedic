"""Detect DNS pollution by cross-checking sensitive domains.

A resolver is considered:
- *polluted*  : returns at least one IP that appears in the GFW poison-IP list
- *suspicious*: response arrives implausibly fast (< POLLUTION_TIME_FLOOR_MS),
                which is the classic fingerprint of a GFW-injected packet
                that beat the legitimate response.
- *failed*    : query timed out / dropped.
"""
from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import dns.exception
import dns.message
import dns.query
import dns.rdatatype

from ..config import KNOWN_POISON_IPS, POLLUTION_TEST_DOMAINS, POLLUTION_TIME_FLOOR_MS
from ..data.public_dns import DnsServer


@dataclass
class PollutionResult:
    server: DnsServer
    polluted_domains: list[str]
    suspicious_domains: list[str]
    failed_domains: list[str]
    sample_results: dict[str, list[str]]

    @property
    def is_polluted(self) -> bool:
        return bool(self.polluted_domains)

    @property
    def looks_clean(self) -> bool:
        return not self.polluted_domains and not self.suspicious_domains


def _resolve(ip: str, domain: str, timeout: float = 2.5) -> tuple[list[str], float | None]:
    q = dns.message.make_query(domain, dns.rdatatype.A)
    start = time.perf_counter()
    try:
        r = dns.query.udp(q, ip, timeout=timeout)
    except (dns.exception.Timeout, dns.exception.DNSException, OSError):
        return [], None
    elapsed = (time.perf_counter() - start) * 1000.0
    ips: list[str] = []
    for rrset in r.answer:
        for item in rrset:
            if item.rdtype == dns.rdatatype.A:
                ips.append(item.to_text())
    return ips, elapsed


def check_pollution(
    server: DnsServer,
    domains: list[str] | None = None,
) -> PollutionResult:
    domains = domains or POLLUTION_TEST_DOMAINS
    polluted: list[str] = []
    suspicious: list[str] = []
    failed: list[str] = []
    samples: dict[str, list[str]] = {}
    for d in domains:
        ips, elapsed = _resolve(server.primary, d)
        samples[d] = ips
        if not ips:
            failed.append(d)
            continue
        if any(ip in KNOWN_POISON_IPS for ip in ips):
            polluted.append(d)
        elif elapsed is not None and elapsed < POLLUTION_TIME_FLOOR_MS:
            suspicious.append(d)
    return PollutionResult(server, polluted, suspicious, failed, samples)


def check_pollution_all(servers: list[DnsServer]) -> list[PollutionResult]:
    if not servers:
        return []
    with ThreadPoolExecutor(max_workers=min(6, len(servers))) as ex:
        return list(ex.map(check_pollution, servers))
