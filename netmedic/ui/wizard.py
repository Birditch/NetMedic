"""First-run / re-pick wizards: language and country.

Both wizards render through the same ``render_page`` chrome as the main
menu so the user always sees a consistent banner + breadcrumb layout.
"""
from __future__ import annotations

from rich import box
from rich.console import Group
from rich.prompt import IntPrompt
from rich.table import Table
from rich.text import Text

from ..data.countries import country_name, supported_codes
from ..i18n import SUPPORTED, t
from .widgets import footer_hint, lang_native_name, render_page


def _selector_table(rows: list[tuple[int, str, str, bool]],
                    cols: tuple[str, str]) -> Table:
    table = Table(
        box=box.SIMPLE_HEAD,
        pad_edge=False,
        expand=True,
    )
    table.add_column("#", justify="right", style="bold cyan", width=3)
    table.add_column(cols[0], style="bold")
    table.add_column(cols[1])
    table.add_column("", justify="right", width=14)
    for n, code, name, marker in rows:
        m = "[green]← current[/green]" if marker else ""
        table.add_row(str(n), code, name, m)
    return table


def ask_language(default: str | None = None) -> str:
    if default not in SUPPORTED:
        default = "en"

    rows = [
        (i, code, lang_native_name(code), code == default)
        for i, code in enumerate(SUPPORTED, 1)
    ]
    body = Group(
        _selector_table(rows, ("Code", "Name")),
        Text(),
        footer_hint("⏎ Enter = keep " + default),
    )
    render_page("language / 语言 / 言語 / 언어 / Язык", body)

    default_idx = SUPPORTED.index(default) + 1
    choice = IntPrompt.ask(
        "\n[bold]Pick a language[/bold]",
        default=default_idx,
        choices=[str(i) for i in range(1, len(SUPPORTED) + 1)],
        show_choices=False,
    )
    return SUPPORTED[choice - 1]


def ask_country(lang: str, default: str | None = None) -> str:
    codes = supported_codes()
    if default not in codes:
        default = "AUTO"

    rows = [
        (i, code, country_name(code, lang), code == default)
        for i, code in enumerate(codes, 1)
    ]
    body = Group(
        _selector_table(rows, ("Code", t("label.country_name"))),
        Text(),
        footer_hint(t("msg.press_enter_keep") if False
                    else "⏎ Enter = keep " + default),
    )
    cfg = {"lang": lang, "country": default}
    render_page(t("label.country_title"), body, cfg)

    default_idx = codes.index(default) + 1
    choice = IntPrompt.ask(
        f"\n[bold]{t('msg.pick_country')}[/bold]",
        default=default_idx,
        choices=[str(i) for i in range(1, len(codes) + 1)],
        show_choices=False,
    )
    return codes[choice - 1]
