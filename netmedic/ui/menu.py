"""Main numbered menu — rendered through the unified page chrome."""
from __future__ import annotations

from rich import box
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..i18n import t
from .widgets import admin_badge, footer_hint, render_page


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


def _menu_table() -> Table:
    table = Table(
        box=box.SIMPLE_HEAD,
        show_lines=False,
        pad_edge=False,
        expand=True,
    )
    table.add_column("#", justify="right", style="bold cyan", width=3)
    table.add_column(t("label.feature"), style="bold")
    table.add_column(t("label.admin"), justify="center", width=14)
    table.add_column(t("label.summary"), overflow="fold", style="dim")
    for i, (key, admin, _) in enumerate(MENU_ITEMS, 1):
        table.add_row(
            str(i),
            t(f"{key}.name"),
            admin_badge(admin),
            t(f"{key}.short"),
        )
    return table


def render(cfg: dict) -> None:
    body = Group(
        _menu_table(),
        Text(),  # spacer
        footer_hint("↑ " + t("msg.pick_action") + "    ⏎ Enter to confirm    Ctrl+C to quit"),
    )
    render_page(t("label.feature"), body, cfg)


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
