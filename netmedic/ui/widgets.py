"""Reusable UI primitives that give every screen a consistent look.

The screen-clear behaviour is *full* — visible area + scrollback. Rich's
default ``console.clear()`` only resets the visible viewport on most
terminals, so the previous page can still be reached by scrolling up.
We send ``\\x1b[H\\x1b[2J\\x1b[3J`` (cursor home + erase display + erase
scrollback) so each page truly replaces the prior one. Modern Windows
Terminal, ConEmu, iTerm2, GNOME Terminal, and the Linux console all
honour this sequence.


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
import os
import sys

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.rule import Rule
from rich.text import Text

from .. import __display_version__
from ..i18n import LOCALES_DIR, t

console = Console(legacy_windows=False)


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
        return f"[bold red]{t('label.need_admin')}[/bold red]"
    return f"[bold green]{t('label.no_admin')}[/bold green]"


# --- page chrome --------------------------------------------------------

def banner() -> Group:
    """Top-of-screen identity banner with version + the *active* tagline."""
    title = Text()
    title.append("NetMedic ", style="bold cyan")
    title.append(f"v{__display_version__}", style="bold yellow")
    # Render the tagline in the user's selected language only — the i18n
    # loader returns the right value for whichever locale is active.
    sub = Text(t("app.tagline"), style="dim")
    return Group(Align.center(title), Align.center(sub))


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


# ESC[H : cursor home
# ESC[2J: erase the entire visible screen
# ESC[3J: erase the scrollback buffer (so user cannot scroll up to peek
#         at the previous page). Together these three give a true page
#         replacement on every modern terminal.
_HARD_CLEAR_SEQ = "\x1b[H\x1b[2J\x1b[3J"


def hard_clear() -> None:
    """Clear visible screen *and* scrollback buffer."""
    if os.name == "nt":
        # Make sure Windows is in VT-processing mode; on modern Windows
        # Terminal / ConEmu it already is, but ``cls`` is a robust fallback
        # that clears both regions on classic conhost.
        os.system("cls")
    sys.stdout.write(_HARD_CLEAR_SEQ)
    sys.stdout.flush()


def render_page(title: str, body: RenderableType, cfg: dict | None = None) -> None:
    """Hard-clear the screen (incl. scrollback) and render a full page."""
    hard_clear()
    console.print(page(title, body, cfg))
