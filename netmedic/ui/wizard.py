"""First-run / re-pick wizards: language and country."""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.table import Table

from ..data.countries import country_name, supported_codes
from ..i18n import SUPPORTED, t
from .widgets import console, lang_native_name


def ask_language(default: str | None = None) -> str:
    if default not in SUPPORTED:
        default = "en"
    console.print(Panel(
        "[bold cyan]NetMedic[/bold cyan] — language / 语言 / 言語 / 언어 / Язык",
        border_style="cyan",
    ))
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Code")
    table.add_column("Name")
    table.add_column("")
    for i, code in enumerate(SUPPORTED, 1):
        marker = "[green]← current[/green]" if code == default else ""
        table.add_row(str(i), code, lang_native_name(code), marker)
    console.print(table)

    default_idx = SUPPORTED.index(default) + 1
    choice = IntPrompt.ask(
        f"\n[bold]Pick a language[/bold] (Enter = keep {default})",
        default=default_idx,
        choices=[str(i) for i in range(1, len(SUPPORTED) + 1)],
        show_choices=False,
    )
    return SUPPORTED[choice - 1]


def ask_country(lang: str, default: str | None = None) -> str:
    codes = supported_codes()
    if default not in codes:
        default = "AUTO"
    console.print(Panel(
        f"[bold cyan]{t('label.country_title')}[/bold cyan]",
        border_style="cyan",
    ))
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Code")
    table.add_column(t("label.country_name"))
    table.add_column("")
    for i, code in enumerate(codes, 1):
        marker = "[green]← current[/green]" if code == default else ""
        table.add_row(str(i), code, country_name(code, lang), marker)
    console.print(table)

    default_idx = codes.index(default) + 1
    choice = IntPrompt.ask(
        f"\n[bold]{t('msg.pick_country')}[/bold] (Enter = {default})",
        default=default_idx,
        choices=[str(i) for i in range(1, len(codes) + 1)],
        show_choices=False,
    )
    return codes[choice - 1]
