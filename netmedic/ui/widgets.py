"""Reusable UI primitives that give every screen a consistent look.

Every interactive page is built from three pieces:

    ┌─ banner ───────────────────────────────────┐
    │           NetMedic v1.0.0                  │
    │  Network Doctor / 网络医生 / ...           │
    └────────────────────────────────────────────┘
        Lang: 简体中文    Country: 中国大陆
    ────────────────── < title > ──────────────────
        <body>
    ────────────────────────────────────────────────
        Footer: hint / shortcut / status

Calling sites construct these via ``page(title, body)`` so layout
stays uniform across the launcher, wizards, and feature handlers.
"""
from __future__ import annotations
import json

from rich import box
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from .. import __version__
from ..i18n import LOCALES_DIR, t

console = Console()


# --- locale meta --------------------------------------------------------

def lang_native_name(code: str) -> str:
    """Return the language's name in its own script (zh-CN -> 简体中文)."""
    try:
        meta = json.loads(
            (LOCALES_DIR / f"{code}.json").read_text(encoding="utf-8")
        ).get("_meta", {})
        return meta.get("name", code)
    except (OSError, json.JSONDecodeError):
        return code


# --- badges -------------------------------------------------------------

def admin_badge(required: bool) -> str:
    if required:
        return f"[bold red]🛡 {t('label.need_admin')}[/bold red]"
    return f"[bold green]✓ {t('label.no_admin')}[/bold green]"


# --- page chrome --------------------------------------------------------

_TAGLINE = "Network Doctor · 网络医生 · ネットワークドクター · 네트워크 닥터 · Сетевой Доктор"


def banner() -> Panel:
    """Top-of-screen identity banner with version + multilingual tagline."""
    title = Text()
    title.append("NetMedic ", style="bold cyan")
    title.append(f"v{__version__}", style="bold yellow")
    sub = Text(_TAGLINE, style="dim")
    return Panel(
        Align.center(Group(title, sub)),
        border_style="cyan",
        box=box.HEAVY,
        padding=(0, 2),
    )


def breadcrumb(cfg: dict) -> Text:
    """Single-line current-context line (lang + country)."""
    from ..data.countries import country_name
    lang = cfg.get("lang", "en")
    country = cfg.get("country", "AUTO")
    line = Text()
    line.append(f"  {t('label.lang')}: ", style="dim")
    line.append(lang_native_name(lang), style="bold")
    line.append("    ", style="dim")
    line.append(f"{t('label.country')}: ", style="dim")
    line.append(country_name(country, lang), style="bold")
    scope = cfg.get("scope")
    if scope:
        line.append("    ", style="dim")
        line.append("Scope: ", style="dim")
        line.append(scope, style="bold")
    return line


def page(title: str, body: RenderableType, cfg: dict | None = None) -> Group:
    """Compose a full page: banner + (optional breadcrumb) + rule + body."""
    parts: list[RenderableType] = [banner()]
    if cfg is not None:
        parts.append(breadcrumb(cfg))
    parts.append(Rule(f"[bold cyan]{title}[/bold cyan]", style="cyan"))
    parts.append(body)
    return Group(*parts)


def footer_hint(text: str) -> Text:
    return Text(text, style="dim italic")


def render_page(title: str, body: RenderableType, cfg: dict | None = None) -> None:
    """Clear screen and render a full page at once."""
    console.clear()
    console.print(page(title, body, cfg))
