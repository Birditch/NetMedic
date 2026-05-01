"""Tunables, test-target lists and the GFW poison-IP table."""
from __future__ import annotations

# How many parallel DNS measurements to run.
DNS_BENCH_WORKERS = 8

# UDP DNS query timeout per attempt (seconds).
DNS_QUERY_TIMEOUT = 2.0

# Number of repeat queries per (server, domain) pair when benchmarking.
DNS_QUERY_REPEAT = 3

# Domains used to benchmark DNS speed (mix of CN + foreign).
SPEED_TEST_DOMAINS = [
    "qq.com",
    "baidu.com",
    "taobao.com",
    "bilibili.com",
    "google.com",
    "github.com",
    "youtube.com",
    "cloudflare.com",
]

# Domains commonly poisoned by the GFW. We use these to detect tampered DNS.
POLLUTION_TEST_DOMAINS = [
    "www.google.com",
    "www.youtube.com",
    "www.facebook.com",
    "twitter.com",
    "wikipedia.org",
]

# Hosts pinged for connectivity / packet-loss check.
CONNECTIVITY_TARGETS = {
    "domestic": [
        ("baidu.com", "百度"),
        ("qq.com", "腾讯 QQ"),
        ("bilibili.com", "Bilibili"),
        ("taobao.com", "淘宝"),
    ],
    "international": [
        ("www.google.com", "Google"),
        ("github.com", "GitHub"),
        ("cloudflare.com", "Cloudflare"),
        ("1.1.1.1", "1.1.1.1 (直连)"),
    ],
}

# IPs known to be returned when the GFW poisons a query. Curated from
# public observations; resolvers that hand back any of these on a sensitive
# domain are flagged "polluted".
KNOWN_POISON_IPS = frozenset({
    "0.0.0.0", "127.0.0.1",
    "8.7.198.45", "37.61.54.158", "46.82.174.68", "59.24.3.173",
    "64.33.88.161", "64.33.99.47", "64.66.163.251", "65.104.202.252",
    "66.45.252.237", "72.14.205.99", "72.14.205.104", "78.16.49.15",
    "93.46.8.89", "128.121.126.139", "159.106.121.75", "169.132.13.103",
    "192.67.198.6", "202.106.1.2", "202.181.7.85", "203.98.7.65",
    "203.161.230.171", "207.12.88.98", "208.56.31.43", "209.36.73.33",
    "209.145.54.50", "209.220.30.174", "211.94.66.147", "213.169.251.35",
    "216.221.188.182", "216.234.179.13", "243.185.187.39",
})

# When a query returns faster than this, it is likely a GFW injected
# response that beat the real one to the wire — or a local resolver cache.
# 5ms is conservative: physical RTT to any overseas DNS via a Japan exit
# is at least 30ms; anything under 5ms cannot be a real cross-region answer.
POLLUTION_TIME_FLOOR_MS = 5.0

# Used by the MTU helper to label results.
MTU_FLOOR = 1280
MTU_NORMAL = 1500
