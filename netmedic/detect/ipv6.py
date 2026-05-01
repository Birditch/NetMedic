"""Quick test: does this machine have working IPv6 connectivity?"""
from __future__ import annotations
import socket


def has_ipv6(timeout: float = 3.0) -> bool:
    """Try a TCP connect to a public v6 endpoint. True if it succeeds."""
    targets = [
        ("2606:4700:4700::1111", 443),  # Cloudflare
        ("2001:4860:4860::8888", 53),   # Google DNS
    ]
    for host, port in targets:
        try:
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
            return True
        except OSError:
            continue
    return False
