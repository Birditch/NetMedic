"""Country / region presets used to weight DNS provider selection.

Each entry maps a country code to:
- ``names``   : display names per UI language
- ``primary`` : DoH provider keys that should appear at the top of the
                bench results when the user is in that country
- ``cn_split``: whether to enable NRPT split for Chinese namespaces
                (only meaningful when the user actually consumes Chinese
                services from this region)
"""
from __future__ import annotations

# Provider keys must match ``netmedic.fix.doh.DOH_PROVIDERS`` keys.
COUNTRIES: dict[str, dict] = {
    "AUTO": {
        "names": {
            "en":    "Auto-detect (by exit IP)",
            "zh-CN": "自动识别 (按出口 IP)",
            "zh-TW": "自動識別 (依出口 IP)",
            "ja":    "自動判定 (出口 IP から)",
            "ko":    "자동 감지 (출구 IP)",
            "ru":    "Авто (по IP выхода)",
        },
        "primary": [],
        "cn_split": True,
    },
    "CN": {
        "names": {
            "en": "China Mainland", "zh-CN": "中国大陆", "zh-TW": "中國大陸",
            "ja": "中国本土", "ko": "중국 본토", "ru": "Материковый Китай",
        },
        "primary": ["AliDNS", "DNSPod", "Cloudflare", "Google"],
        "cn_split": True,
    },
    "JP": {
        "names": {
            "en": "Japan", "zh-CN": "日本", "zh-TW": "日本",
            "ja": "日本", "ko": "일본", "ru": "Япония",
        },
        "primary": ["Cloudflare", "Google", "Quad101", "AliDNS"],
        "cn_split": True,
    },
    "TW": {
        "names": {
            "en": "Taiwan", "zh-CN": "台湾", "zh-TW": "台灣",
            "ja": "台湾", "ko": "대만", "ru": "Тайвань",
        },
        "primary": ["Quad101", "Cloudflare", "Google"],
        "cn_split": False,
    },
    "HK": {
        "names": {
            "en": "Hong Kong", "zh-CN": "香港", "zh-TW": "香港",
            "ja": "香港", "ko": "홍콩", "ru": "Гонконг",
        },
        "primary": ["Cloudflare", "Google", "Quad101"],
        "cn_split": False,
    },
    "KR": {
        "names": {
            "en": "South Korea", "zh-CN": "韩国", "zh-TW": "南韓",
            "ja": "韓国", "ko": "대한민국", "ru": "Южная Корея",
        },
        "primary": ["Cloudflare", "Google", "Quad9"],
        "cn_split": False,
    },
    "US": {
        "names": {
            "en": "United States", "zh-CN": "美国", "zh-TW": "美國",
            "ja": "アメリカ", "ko": "미국", "ru": "США",
        },
        "primary": ["Cloudflare", "Google", "Quad9", "OpenDNS"],
        "cn_split": False,
    },
    "EU": {
        "names": {
            "en": "Europe (general)", "zh-CN": "欧洲 (通用)", "zh-TW": "歐洲 (通用)",
            "ja": "欧州 (一般)", "ko": "유럽 (일반)", "ru": "Европа (общая)",
        },
        "primary": ["Cloudflare", "Quad9", "Google", "DNS.SB"],
        "cn_split": False,
    },
    "RU": {
        "names": {
            "en": "Russia", "zh-CN": "俄罗斯", "zh-TW": "俄羅斯",
            "ja": "ロシア", "ko": "러시아", "ru": "Россия",
        },
        "primary": ["YandexDNS", "Cloudflare", "Google"],
        "cn_split": False,
    },
    "SG": {
        "names": {
            "en": "Singapore", "zh-CN": "新加坡", "zh-TW": "新加坡",
            "ja": "シンガポール", "ko": "싱가포르", "ru": "Сингапур",
        },
        "primary": ["Cloudflare", "Google", "Quad9"],
        "cn_split": False,
    },
}


def country_name(code: str, lang: str) -> str:
    info = COUNTRIES.get(code, {})
    names = info.get("names", {})
    return names.get(lang) or names.get("en") or code


def supported_codes() -> list[str]:
    return list(COUNTRIES.keys())
