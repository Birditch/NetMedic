"""Main numbered menu.

Two responsibilities now:

- ``render_and_pick(cfg)`` — owns the main-menu loop. Renders inside a
  ``rich.live.Live`` so the layout auto-redraws at ~8 fps; that means
  any terminal resize is picked up within ~125 ms without the user
  having to do anything. A non-blocking key reader (``ui.keys``) runs
  alongside Live, building a small input buffer that is itself drawn
  in the footer so the user can see what they're typing.

- ``show_feature_intro(idx)`` — the per-feature confirmation panel.
"""
from __future__ import annotations

import time

from rich import box
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ..i18n import t
from .keys import cbreak_mode, getch_nowait
from .widgets import (
    admin_badge,
    banner,
    breadcrumb,
    console,
    hard_clear,
    render_page,
)


# (translation-key-prefix, admin_required, action_id)
MENU_ITEMS: list[tuple[str, bool, str]] = [
    ("menu.lang",      False, "switch_lang"),
    ("menu.country",   False, "switch_country"),
    ("menu.check",     False, "check"),
    ("menu.recommend", False, "recommend"),
    ("menu.apply",     True,  "apply"),
    ("menu.restore",   True,  "restore"),
    ("menu.force_doh", True,  "force_doh"),
    ("menu.bench_doh", False, "bench_doh"),
    ("menu.flush",     False, "flush"),
    ("menu.status",    False, "status"),
    ("menu.hosts_fix", True,  "hosts_repair"),
    ("menu.outage",    False, "outage_diagnose"),
    ("menu.hijack",    False, "hijack_check"),
    ("menu.exit",      False, "exit"),
]


# --- status snapshot ---------------------------------------------------

def _gather_status(cfg: dict) -> dict[str, str]:
    """Cheap one-shot status snapshot for every menu action.

    Must stay fast — anything that calls PowerShell or makes a network
    request belongs inside the corresponding command, not here.
    """
    status: dict[str, str] = {action: "—" for _, _, action in MENU_ITEMS}

    from .widgets import lang_native_name
    from ..data.countries import country_name

    lang = cfg.get("lang", "en")
    country = cfg.get("country", "AUTO")
    status["switch_lang"]    = f"[bold]{lang_native_name(lang)}[/bold]"
    status["switch_country"] = f"[bold]{country_name(country, lang)}[/bold]"

    if cfg.get("scope"):
        status["force_doh"] = f"[dim]scope: {cfg['scope']}[/dim]"
    if cfg.get("set_ipv6") is False:
        ipv6 = "off"
    elif cfg.get("set_ipv6") is True:
        ipv6 = "on"
    else:
        ipv6 = ""
    if ipv6:
        cur = status["force_doh"]
        sep = "  " if cur and cur != "—" else ""
        status["force_doh"] = f"{cur}{sep}[dim]v6: {ipv6}[/dim]"

    try:
        from ..fix.backup import latest_backup
        if latest_backup():
            status["apply"]   = "[dim]backup ready[/dim]"
            status["restore"] = "[green]restorable[/green]"
        else:
            status["apply"]   = "[dim]no prior apply[/dim]"
            status["restore"] = "[dim]nothing yet[/dim]"
    except Exception:  # noqa: BLE001
        pass

    try:
        from ..fix.hosts_repair import HOSTS_PATH, analyze
        info = analyze(HOSTS_PATH)
        if info.issues:
            status["hosts_repair"] = f"[yellow]{len(info.issues)} issue(s)[/yellow]"
        else:
            status["hosts_repair"] = "[green]clean[/green]"
    except Exception:  # noqa: BLE001
        pass

    return status


# --- rendering ---------------------------------------------------------

def _menu_table(status: dict[str, str]) -> Table:
    table = Table(
        box=box.SIMPLE_HEAD,
        show_lines=False,
        pad_edge=False,
        expand=True,
    )
    table.add_column("#", justify="right", style="bold cyan", width=3)
    table.add_column(t("label.feature"), style="bold", no_wrap=False)
    table.add_column(t("label.admin"), justify="center", width=14)
    table.add_column(t("label.col.status") if "label.col.status" else "Status",
                     justify="left", overflow="fold")
    table.add_column(t("label.summary"), overflow="fold", style="dim")
    for i, (key, admin, action) in enumerate(MENU_ITEMS, 1):
        table.add_row(
            str(i),
            t(f"{key}.name"),
            admin_badge(admin),
            status.get(action, "—"),
            t(f"{key}.short"),
        )
    return table


def _menu_renderable(cfg: dict, status: dict[str, str], buf: str) -> Group:
    prompt = Text()
    prompt.append("\n")
    prompt.append(t("msg.pick_action"), style="bold")
    prompt.append("  ")
    prompt.append(f"(1-{len(MENU_ITEMS)}, Enter=confirm, Esc=quit)", style="dim")
    prompt.append("\n  > ")
    prompt.append(buf or " ", style="bold yellow on grey15")
    return Group(
        banner(),
        breadcrumb(cfg),
        Rule(f"[bold cyan]{t('label.feature')}[/bold cyan]", style="cyan"),
        _menu_table(status),
        prompt,
    )


def render_and_pick(cfg: dict) -> int | None:
    """Render the main menu and wait for a number selection.

    Returns the 1-based menu index, or ``None`` when the user pressed
    Esc / Ctrl+C. Auto-redraws ~8 fps so terminal resizes are picked up
    immediately.
    """
    status = _gather_status(cfg)
    n = len(MENU_ITEMS)
    buf = ""

    hard_clear()
    with cbreak_mode():
        with Live(
            _menu_renderable(cfg, status, buf),
            console=console,
            screen=True,
            refresh_per_second=8,
            auto_refresh=True,
            transient=False,
        ) as live:
            while True:
                ch = getch_nowait()
                if ch is None:
                    # Idle tick — Live's auto_refresh handles resize for us.
                    time.sleep(0.03)
                    continue

                if ch in ("\r", "\n"):
                    if buf.isdigit():
                        v = int(buf)
                        if 1 <= v <= n:
                            return v
                    buf = ""
                elif ch in ("\x1b", "\x03"):  # Esc, Ctrl+C
                    return None
                elif ch in ("\x08", "\x7f"):  # backspace / del
                    buf = buf[:-1]
                elif ch.isdigit():
                    buf += ch
                    # auto-confirm once buf can no longer grow into a valid
                    # higher number (e.g. typed "9" when n=14 isn't enough,
                    # but typed "5" when n=14 is unambiguous).
                    if int(buf) > n // 10 and int(buf) * 10 > n:
                        v = int(buf)
                        if 1 <= v <= n:
                            return v
                        buf = ""
                live.update(_menu_renderable(cfg, status, buf))


def show_feature_intro(idx: int) -> bool:
    key, admin, _ = MENU_ITEMS[idx]
    title = f"#{idx + 1} · {t(f'{key}.name')}"

    body = Group(
        Panel(
            t(f"{key}.long"),
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        ),
        Align.left(admin_badge(admin)),
    )
    render_page(title, body)

    return Prompt.ask(
        f"\n[bold]{t('msg.run_now')}[/bold]",
        choices=["y", "n"],
        default="y",
    ).lower() == "y"
