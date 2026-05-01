"""Simple JSON-backed i18n loader.

Locale JSON files live in ``D:/NetMedic/locales/<lang>.json``. The active
locale is selected (in order of priority):

1. ``set_lang()`` called explicitly (e.g. from the ``--lang`` CLI option).
2. Environment variable ``NETMEDIC_LANG``.
3. The OS locale, mapped to the closest supported language.
4. Fallback: ``en``.
"""
from __future__ import annotations

import json
import locale as _stdlocale
import os
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent / "locales"

SUPPORTED: list[str] = ["en", "zh-CN", "zh-TW", "ja", "ko", "ru"]
DEFAULT_LANG = "en"

_translations: dict[str, str] = {}
_current_lang: str = DEFAULT_LANG


def _detect_lang() -> str:
    env = os.environ.get("NETMEDIC_LANG")
    if env in SUPPORTED:
        return env
    try:
        sys_lang, _ = _stdlocale.getlocale()
    except (TypeError, ValueError):
        sys_lang = None
    if not sys_lang:
        return DEFAULT_LANG
    s = sys_lang.replace("_", "-").lower()
    if s.startswith("zh"):
        return "zh-TW" if ("tw" in s or "hk" in s or "hant" in s) else "zh-CN"
    if s.startswith("ja"):
        return "ja"
    if s.startswith("ko"):
        return "ko"
    if s.startswith("ru"):
        return "ru"
    if s.startswith("en"):
        return "en"
    return DEFAULT_LANG


def set_lang(lang: str | None) -> str:
    """Activate a language. Returns the language actually loaded."""
    global _current_lang, _translations
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    path = LOCALES_DIR / f"{lang}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _translations = {k: v for k, v in data.items() if not k.startswith("_")}
        _current_lang = lang
    except (OSError, json.JSONDecodeError):
        _translations = {}
        _current_lang = DEFAULT_LANG
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Translate ``key`` with optional ``str.format`` kwargs.

    Falls back to the key itself if not found, so missing translations are
    obvious in the output instead of crashing.
    """
    val = _translations.get(key, key)
    if kwargs:
        try:
            return val.format(**kwargs)
        except (KeyError, IndexError):
            return val
    return val


def current_lang() -> str:
    return _current_lang


# Auto-init at import time so plain ``from .i18n import t`` works.
set_lang(_detect_lang())
