"""Apply or reset DNS server addresses on a Windows interface."""
from __future__ import annotations

from ..utils import run_powershell


def set_dns(ifindex: int, servers: list[str]) -> None:
    if not servers:
        raise ValueError("set_dns: servers list is empty")
    quoted = ",".join(f'"{ip}"' for ip in servers)
    rc, out, err = run_powershell(
        f"Set-DnsClientServerAddress -InterfaceIndex {ifindex} "
        f"-ServerAddresses ({quoted}) -ErrorAction Stop"
    )
    if rc != 0:
        raise RuntimeError(f"set_dns 失败: {err.strip() or out.strip()}")


def reset_dns(ifindex: int) -> None:
    rc, out, err = run_powershell(
        f"Set-DnsClientServerAddress -InterfaceIndex {ifindex} "
        f"-ResetServerAddresses -ErrorAction Stop"
    )
    if rc != 0:
        raise RuntimeError(f"reset_dns 失败: {err.strip() or out.strip()}")
