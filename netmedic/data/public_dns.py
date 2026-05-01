"""Curated list of public DNS servers benchmarked by NetMedic.

Two pools:
- ``CN_SERVERS``  : best for resolving Chinese services (will give China-side
                    IPs that the soft router routes directly, not via Japan).
- ``INTL_SERVERS``: best for resolving foreign services from a Japan exit
                    (anycast / privacy-focused / uncensored).
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DnsServer:
    name: str
    primary: str
    secondary: str | None
    region: str  # "cn" or "intl"
    operator: str
    description: str


CN_SERVERS: list[DnsServer] = [
    DnsServer("AliDNS", "223.5.5.5", "223.6.6.6", "cn", "阿里巴巴",
              "国内解析速度优秀, 推荐用于国内域名"),
    DnsServer("DNSPod", "119.29.29.29", "182.254.116.116", "cn", "腾讯",
              "对腾讯系 (QQ/微信) 解析最优"),
    DnsServer("114DNS", "114.114.114.114", "114.114.115.115", "cn", "南京信风",
              "老牌国内 DNS, 稳定但偶有劫持"),
    DnsServer("BaiduDNS", "180.76.76.76", None, "cn", "百度",
              "百度公共 DNS"),
    DnsServer("CNNIC", "1.2.4.8", "210.2.4.8", "cn", "CNNIC",
              "中国互联网络信息中心"),
]

INTL_SERVERS: list[DnsServer] = [
    DnsServer("Cloudflare", "1.1.1.1", "1.0.0.1", "intl", "Cloudflare",
              "全球 anycast, 隐私强, 经日本出口速度优秀, 首选境外 DNS"),
    DnsServer("Google", "8.8.8.8", "8.8.4.4", "intl", "Google",
              "Google Public DNS, 解析准确性极高"),
    DnsServer("Quad9", "9.9.9.9", "149.112.112.112", "intl", "IBM/Quad9",
              "带恶意域名拦截, 隐私好"),
    DnsServer("OpenDNS", "208.67.222.222", "208.67.220.220", "intl", "Cisco",
              "Cisco OpenDNS"),
    DnsServer("AdGuard", "94.140.14.14", "94.140.15.15", "intl", "AdGuard",
              "广告/追踪过滤"),
    DnsServer("DNS.SB", "185.222.222.222", "45.11.45.11", "intl", "DNS.SB",
              "无日志, 速度好"),
]

ALL_SERVERS: list[DnsServer] = CN_SERVERS + INTL_SERVERS
