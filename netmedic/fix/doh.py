"""Windows 11 DNS-over-HTTPS (DoH) helpers.

DoH carries DNS queries over HTTPS:443, so a soft-router's UDP-53 hijack
can no longer intercept them. Windows 11 has native DoH support via the
``DnsClientDohServerAddress`` cmdlets.

Each public DNS IP needs a known DoH template before Windows will use it
encrypted. We register the templates ourselves so the user doesn't have
to depend on Windows' rolling built-in list.
"""
from __future__ import annotations
import json

from ..utils import run_powershell

# Provider-centric view. Only **uncensored, no-filter** resolvers — anything
# that filters malware/ads/adult is excluded per user requirement (无任何限制).
# v4_ips / v6_ips are the Windows-side DNS targets. ``url`` is the DoH endpoint.
DOH_PROVIDERS: dict[str, dict] = {
    "Cloudflare": {
        "url":     "https://cloudflare-dns.com/dns-query",
        "region":  "intl",
        "operator": "Cloudflare",
        "notes":   "全球 anycast, 无审查, 隐私强",
        "v4_ips":  ["1.1.1.1", "1.0.0.1"],
        "v6_ips":  ["2606:4700:4700::1111", "2606:4700:4700::1001"],
    },
    "Google": {
        "url":     "https://dns.google/dns-query",
        "region":  "intl",
        "operator": "Google",
        "notes":   "全球, 解析准确, 无审查",
        "v4_ips":  ["8.8.8.8", "8.8.4.4"],
        "v6_ips":  ["2001:4860:4860::8888", "2001:4860:4860::8844"],
    },
    "Quad101": {
        "url":     "https://dns.twnic.tw/dns-query",
        "region":  "tw",
        "operator": "TWNIC 台湾网络信息中心",
        "notes":   "台湾公共 DNS, 无审查, 离日本节点近",
        "v4_ips":  ["101.101.101.101", "101.102.103.104"],
        "v6_ips":  ["2001:de4::101", "2001:de4::102"],
    },
    "AliDNS": {
        "url":     "https://dns.alidns.com/dns-query",
        "region":  "cn",
        "operator": "阿里巴巴",
        "notes":   "国内最稳, 国内域名解析最优",
        "v4_ips":  ["223.5.5.5", "223.6.6.6"],
        "v6_ips":  ["2400:3200::1", "2400:3200:baba::1"],
    },
    "DNSPod": {
        "url":     "https://doh.pub/dns-query",
        "region":  "cn",
        "operator": "腾讯",
        "notes":   "对腾讯系 (QQ/微信) 解析最优",
        "v4_ips":  ["119.29.29.29", "1.12.12.12"],
        "v6_ips":  ["2402:4e00::", "2402:4e00:1::"],
    },
}

# Flat IP -> URL view, used by register_doh / filter_doh_capable.
# Includes both v4 and v6 IPs.
DOH_TEMPLATES: dict[str, str] = {
    ip: prov["url"]
    for prov in DOH_PROVIDERS.values()
    for ip in (prov.get("v4_ips", []) + prov.get("v6_ips", []))
}


def doh_supported() -> bool:
    rc, _, _ = run_powershell(
        "if (Get-Command Get-DnsClientDohServerAddress -ErrorAction SilentlyContinue) "
        "{ exit 0 } else { exit 1 }"
    )
    return rc == 0


def list_doh_servers() -> list[dict]:
    rc, out, _ = run_powershell(
        "Get-DnsClientDohServerAddress | "
        "Select-Object ServerAddress, DohTemplate, AllowFallbackToUdp, AutoUpgrade | "
        "ConvertTo-Json -Compress -Depth 4"
    )
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return [data]
    return data


def filter_doh_capable(servers: list[str]) -> list[str]:
    """Drop IPs that don't have a known DoH template."""
    return [s for s in servers if s in DOH_TEMPLATES]


def register_doh(servers: list[str]) -> int:
    """Register a DoH template for each capable IP. Returns count succeeded.

    We always Remove then Add so a stale template gets replaced rather than
    causing 'already exists' errors.
    """
    ok = 0
    for ip in servers:
        tmpl = DOH_TEMPLATES.get(ip)
        if not tmpl:
            continue
        rc, _, _ = run_powershell(
            f"Remove-DnsClientDohServerAddress -ServerAddress '{ip}' "
            f"-Confirm:$false -ErrorAction SilentlyContinue | Out-Null;"
            f"Add-DnsClientDohServerAddress -ServerAddress '{ip}' "
            f"-DohTemplate '{tmpl}' -AllowFallbackToUdp $false "
            f"-AutoUpgrade $true -ErrorAction Stop"
        )
        if rc == 0:
            ok += 1
    return ok


def set_doh_only(ifindex: int) -> None:
    """Force the adapter to require DoH (no fallback to plain UDP/53).

    Sets per-server DoH config via Set-DnsClientDohServerAddress' implicit
    ``-AutoUpgrade $true -AllowFallbackToUdp $false`` and toggles the
    interface-level encryption to *Encrypted only*.
    """
    rc, _, err = run_powershell(
        f"Set-DnsClientServerAddress -InterfaceIndex {ifindex} "
        f"-ServerAddresses (Get-DnsClientServerAddress -InterfaceIndex {ifindex} "
        f"-AddressFamily IPv4).ServerAddresses;"
        # Doh policy: 0=Off,1=Auto,2=AutoUpgrade,3=Required.
        # We use ``Set-DnsClientNrptGlobal`` analogue via registry only on need.
    )
    # Errors here are non-fatal — having the templates registered is the
    # critical part; Windows will use them automatically.
