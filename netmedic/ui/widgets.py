"""Tiny reusable UI helpers."""
from __future__ import annotations
import json

from rich.console import Console

from ..i18n import LOCALES_DIR, t

console = Console()


def lang_native_name(code: str) -> str:
    """Return the language's name in its own script (zh-CN -> 简体中文)."""
    try:
        meta = json.loads(
            (LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8")
        ).get("_meta", {})
        return meta.get("name", code)
    except (OSError, json.JSONDecodeError):
        return code


def admin_badge(required: bool) -> str:
    if required:
        return f"[red]🛡 {t('label.need_admin')}[/red]"
    return f"[green]✓ {t('label.no_admin')}[/green]"
