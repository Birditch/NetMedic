"""Main numbered menu.

Two responsibilities:

- ``render_and_pick(cfg)`` — render the main menu and read a numeric
  choice.
- ``show_feature_intro(idx)`` — the per-feature confirmation panel.
"""
from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..i18n import t
from .widgets import (
    admin_badge,
    console,
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
    table.add_column(t("label.admin"), justify="center", width=8, no_wrap=True)
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


def render_and_pick(cfg: dict) -> int | None:
    """Render the main menu and wait for a number selection.

    Returns the 1-based menu index, or ``None`` when the user chooses
    to quit.
    """
    status = _gather_status(cfg)
    n = len(MENU_ITEMS)

    # Rich Live's alternate-screen auto refresh flickers badly in some
    # PowerShell/conhost setups and can leave repeated border lines on the
    # screen. A static render plus normal prompt is less clever, but stable.
    render_page(t("label.feature"), Group(_menu_table(status)), cfg)
    while True:
        raw = Prompt.ask(
            f"\n[bold]{t('msg.pick_action')}[/bold]",
            default="",
            show_default=False,
        ).strip()
        if not raw:
            continue
        if raw.lower() in {"q", "quit", "exit"}:
            return None
        if raw.isdigit():
            v = int(raw)
            if 1 <= v <= n:
                return v
        console.print(f"[red]请输入 1-{n} 之间的编号，或输入 q 退出。[/red]")


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
