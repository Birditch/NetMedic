"""Top-level orchestration: bootstrap-clean entry, first-run wizards, menu loop.

The heavy lifting lives in:
- ``netmedic.ui.wizard``  — language / country pickers
- ``netmedic.ui.menu``    — menu rendering and intro panel
- ``netmedic.ui.actions`` — dispatch table
"""
from __future__ import annotations

from rich.prompt import IntPrompt, Prompt

from . import user_config
from .i18n import set_lang, t
from .ui import actions, menu
from .ui.widgets import console
from .ui.wizard import ask_country, ask_language


def _first_run(cfg: dict) -> dict:
    if not cfg.get("lang"):
        cfg["lang"] = ask_language()
        user_config.save(cfg)
    set_lang(cfg["lang"])
    if not cfg.get("country"):
        cfg["country"] = ask_country(cfg["lang"])
        user_config.save(cfg)
    return cfg


def _menu_loop(cfg: dict) -> None:
    items = menu.MENU_ITEMS
    while True:
        menu.render(cfg)  # internally clears the screen first
        try:
            choice = IntPrompt.ask(
                f"\n[bold]{t('msg.pick_action')}[/bold]",
                choices=[str(i) for i in range(1, len(items) + 1)],
                show_choices=False,
            )
        except (KeyboardInterrupt, EOFError):
            console.print()
            return

        idx = choice - 1
        action = items[idx][2]

        # Lang / country / exit don't need a confirmation panel.
        if action in {"switch_lang", "switch_country", "exit"}:
            cfg = actions.dispatch(action, cfg)
            continue

        if not menu.show_feature_intro(idx):
            continue
        cfg = actions.dispatch(action, cfg)
        Prompt.ask(f"\n[dim]{t('msg.press_enter')}[/dim]", default="")


def run(argv: list[str]) -> None:
    """Entry point invoked from ``run.py`` after dependency bootstrap."""
    if argv:
        # Direct CLI usage: forward to the legacy typer app.
        from .cli import main as cli_main
        return cli_main()
    cfg = _first_run(user_config.load())
    _menu_loop(cfg)
