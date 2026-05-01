"""Main numbered menu rendering and feature intro."""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from .. import __version__
from ..data.countries import country_name
from ..i18n import t
from .widgets import admin_badge, console, lang_native_name


# (translation-key-prefix, admin_required, action_id)
# Action IDs are dispatched by ``ui.actions.dispatch``.
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


def render(cfg: dict) -> None:
    """Print the header + numbered menu table."""
    header = Text.assemble(
        ("NetMedic v", "bold cyan"),
        (__version__, "bold yellow"),
        ("  —  ", "dim"),
        (t("app.tagline"), "bold cyan"),
    )
    console.print(Panel(header, border_style="cyan"))

    sub = (
        f"[dim]{t('label.lang')}: [/dim]{lang_native_name(cfg.get('lang', 'en'))}"
        "    "
        f"[dim]{t('label.country')}: [/dim]"
        f"{country_name(cfg.get('country', 'AUTO'), cfg.get('lang', 'en'))}"
    )
    console.print(sub)
    console.print()

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column(t("label.feature"))
    table.add_column(t("label.admin"))
    table.add_column(t("label.summary"), overflow="fold")
    for i, (key, admin, _) in enumerate(MENU_ITEMS, 1):
        table.add_row(
            str(i),
            t(f"{key}.name"),
            admin_badge(admin),
            t(f"{key}.short"),
        )
    console.print(table)


def show_feature_intro(idx: int) -> bool:
    """Print full localized intro for a feature, ask y/n confirmation."""
    key, admin, _ = MENU_ITEMS[idx]
    console.rule(f"[bold cyan]#{idx + 1} · {t(f'{key}.name')}[/bold cyan]")
    console.print(Panel(t(f"{key}.long"), border_style="cyan"))
    console.print(admin_badge(admin))
    console.print()
    return Prompt.ask(
        f"[bold]{t('msg.run_now')}[/bold]",
        choices=["y", "n"],
        default="y",
    ).lower() == "y"
