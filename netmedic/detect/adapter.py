"""Discover the active IPv4 network adapter (the one with the default route)."""
from __future__ import annotations
import json
from dataclasses import dataclass

from ..utils import run_powershell


@dataclass
class AdapterInfo:
    alias: str
    ifindex: int
    description: str
    ipv4: str | None
    gateway: str | None
    dns_servers: list[str]


_SCRIPT = r"""
$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
    Where-Object { $_.NextHop -ne '0.0.0.0' -and $_.NextHop -ne '::' } |
    Sort-Object RouteMetric, ifMetric |
    Select-Object -First 1
if (-not $route) { return }
$if = Get-NetAdapter -InterfaceIndex $route.ifIndex -ErrorAction SilentlyContinue
if (-not $if) { return }
$ipcfg = Get-NetIPAddress -InterfaceIndex $route.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
$dns = (Get-DnsClientServerAddress -InterfaceIndex $route.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).ServerAddresses
[PSCustomObject]@{
    Alias       = $if.Name
    IfIndex     = [int]$route.ifIndex
    Description = $if.InterfaceDescription
    IPv4        = if ($ipcfg) { $ipcfg.IPAddress } else { $null }
    Gateway     = $route.NextHop
    DNS         = @($dns)
} | ConvertTo-Json -Compress
"""


def get_active_adapter() -> AdapterInfo | None:
    rc, out, err = run_powershell(_SCRIPT)
    if rc != 0 or not out.strip():
        return None
    try:
        data = json.loads(out.strip())
    except json.JSONDecodeError:
        return None
    dns = data.get("DNS") or []
    if isinstance(dns, str):
        dns = [dns]
    return AdapterInfo(
        alias=data.get("Alias", ""),
        ifindex=int(data.get("IfIndex", 0)),
        description=data.get("Description", ""),
        ipv4=data.get("IPv4"),
        gateway=data.get("Gateway"),
        dns_servers=list(dns),
    )
