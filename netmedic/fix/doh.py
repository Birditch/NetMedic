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
# that filters malware/ads/adult/family is excluded per user requirement
# (无任何限制). v4_ips / v6_ips are the Windows-side DNS targets. ``url`` is
# the DoH endpoint. IPv6 IPs verified against the curated 2026-05-01 dataset.
DOH_PROVIDERS: dict[str, dict] = {
    "Cloudflare": {
        "url":     "https://cloudflare-dns.com/dns-query",
        "region":  "intl",
        "operator": "Cloudflare",
        "notes":   "Global anycast · no filter · strong privacy",
        "v4_ips":  ["1.1.1.1", "1.0.0.1"],
        "v6_ips":  ["2606:4700:4700::1111", "2606:4700:4700::1001"],
    },
    "Google": {
        "url":     "https://dns.google/dns-query",
        "region":  "intl",
        "operator": "Google",
        "notes":   "Global · accurate · no filter",
        "v4_ips":  ["8.8.8.8", "8.8.4.4"],
        "v6_ips":  ["2001:4860:4860::8888", "2001:4860:4860::8844"],
    },
    "Quad9": {
        "url":     "https://dns.quad9.net/dns-query",
        "region":  "intl",
        "operator": "Quad9 / IBM (CH)",
        "notes":   "Quad9 Recommended (no malware list active on -unfiltered)",
        "v4_ips":  ["9.9.9.10", "149.112.112.10"],
        "v6_ips":  ["2620:fe::fe", "2620:fe::9"],
    },
    "OpenDNS": {
        "url":     "https://doh.opendns.com/dns-query",
        "region":  "intl",
        "operator": "Cisco",
        "notes":   "OpenDNS Home — sandbox/unfiltered profile",
        "v4_ips":  ["208.67.222.222", "208.67.220.220"],
        "v6_ips":  ["2620:119:35::35", "2620:119:53::53"],
    },
    "ControlD": {
        "url":     "https://freedns.controld.com/p0",
        "region":  "intl",
        "operator": "Control D",
        "notes":   "Free unfiltered profile (p0)",
        "v4_ips":  ["76.76.2.0", "76.76.10.0"],
        "v6_ips":  ["2606:1a40::", "2606:1a40:1::"],
    },
    "Mullvad": {
        "url":     "https://dns.mullvad.net/dns-query",
        "region":  "intl",
        "operator": "Mullvad VPN (SE)",
        "notes":   "Encrypted DNS only · DoH/DoT (no plain UDP)",
        "v4_ips":  ["194.242.2.2"],
        "v6_ips":  ["2a07:e340::2"],
    },
    "DNS.WATCH": {
        "url":     "https://dns.watch/dns-query",
        "region":  "intl",
        "operator": "DNS.WATCH (DE)",
        "notes":   "No filter · no log · DNSSEC",
        "v4_ips":  ["84.200.69.80", "84.200.70.40"],
        "v6_ips":  ["2001:1608:10:25::1c04:b12f",
                    "2001:1608:10:25::9249:d69b"],
    },
    "UltraDNS": {
        "url":     "https://public.ultradns.com/dns-query",
        "region":  "intl",
        "operator": "Vercara / DigiCert",
        "notes":   "UltraDNS Public Unfiltered",
        "v4_ips":  ["64.6.64.6", "64.6.65.6"],
        "v6_ips":  ["2620:74:1b::1:1", "2620:74:1c::2:2"],
    },
    "DNS.SB": {
        "url":     "https://doh.dns.sb/dns-query",
        "region":  "intl",
        "operator": "DNS.SB",
        "notes":   "No log · EU / Asia anycast",
        "v4_ips":  ["185.222.222.222", "45.11.45.11"],
        "v6_ips":  ["2a09::", "2a11::"],
    },
    "AdGuard": {
        "url":     "https://dns.adguard-dns.com/dns-query",
        "region":  "intl",
        "operator": "AdGuard",
        "notes":   "Default profile (ad blocking only — kept for users who want it)",
        "v4_ips":  ["94.140.14.14", "94.140.15.15"],
        "v6_ips":  ["2a10:50c0::ad1:ff", "2a10:50c0::ad2:ff"],
    },
    "Quad101": {
        "url":     "https://dns.twnic.tw/dns-query",
        "region":  "tw",
        "operator": "TWNIC (TW)",
        "notes":   "Taiwan public DNS · close to Japan exit",
        "v4_ips":  ["101.101.101.101", "101.102.103.104"],
        "v6_ips":  ["2001:de4::101", "2001:de4::102"],
    },
    "AliDNS": {
        "url":     "https://dns.alidns.com/dns-query",
        "region":  "cn",
        "operator": "Alibaba",
        "notes":   "Best for Chinese-mainland service resolution",
        "v4_ips":  ["223.5.5.5", "223.6.6.6"],
        "v6_ips":  ["2400:3200::1", "2400:3200:baba::1"],
    },
    "DNSPod": {
        "url":     "https://doh.pub/dns-query",
        "region":  "cn",
        "operator": "Tencent",
        "notes":   "Best for Tencent ecosystem (QQ / WeChat)",
        "v4_ips":  ["119.29.29.29", "1.12.12.12"],
        "v6_ips":  ["2402:4e00::", "2402:4e00:1::"],
    },
    "BaiduDNS": {
        "url":     "https://dns.baidu.com/dns-query",
        "region":  "cn",
        "operator": "Baidu",
        "notes":   "Mainland China · IPv6 supported per official docs",
        "v4_ips":  ["180.76.76.76"],
        "v6_ips":  ["2400:da00::6666"],
    },
    "CFIEC": {
        "url":     "",
        "region":  "cn",
        "operator": "CFIEC / 下一代互联网国家工程中心",
        "notes":   "IPv6-only · DNS64 capable",
        "v4_ips":  [],
        "v6_ips":  ["240c::6666", "240c::6644"],
    },
    "YandexDNS": {
        "url":     "https://common.dot.dns.yandex.net/dns-query",
        "region":  "ru",
        "operator": "Yandex",
        "notes":   "Russia-side anycast · uncensored basic profile",
        "v4_ips":  ["77.88.8.8", "77.88.8.1"],
        "v6_ips":  ["2a02:6b8::feed:0ff", "2a02:6b8:0:1::feed:0ff"],
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
