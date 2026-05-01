"""Dispatch table — runs the work behind each menu item."""
from __future__ import annotations

import sys

from rich import box
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from .. import user_config
from ..i18n import set_lang, t
from .widgets import console
from .wizard import ask_country, ask_language


# Map menu action_id -> typer subcommand argv. Only listed actions
# are forwarded to the typer CLI; the rest are handled inline below.
# ``force_doh`` is *not* in this table — its menu wrapper asks the user
# for scope and IPv6 preference first, then dispatches with flags.
_TYPER_DELEGATES: dict[str, list[str]] = {
    "check":      ["check"],
    "recommend":  ["recommend"],
    "apply":      ["apply"],
    "restore":    ["restore"],
    "bench_doh":  ["bench-doh"],
    "flush":      ["flush"],
    "status":     ["status"],
}


def _run_typer(argv: list[str]) -> None:
    """Invoke the typer CLI as if from the shell, leaving stdout intact."""
    from ..cli import app as typer_app
    saved = sys.argv
    try:
        sys.argv = ["netmedic", *argv]
        try:
            typer_app()
        except SystemExit:
            pass
    finally:
        sys.argv = saved


def _ask_scope(default: str) -> str:
    """Prompt for DoH candidate scope (1=country / 2=country+majors / 3=all)."""
    table = Table(title=t("label.scope_title"), box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="cyan")
    table.add_column(t("label.scope_name"))
    table.add_column(t("label.summary"), overflow="fold")
    rows = [
        ("country",        t("scope.country.name"),        t("scope.country.short")),
        ("country+majors", t("scope.country_plus.name"),   t("scope.country_plus.short")),
        ("all",            t("scope.all.name"),            t("scope.all.short")),
    ]
    for i, (_, name, short) in enumerate(rows, 1):
        marker = "  [green]← current[/green]" if rows[i - 1][0] == default else ""
        table.add_row(str(i), name + marker, short)
    console.print(table)

    default_idx = next((i + 1 for i, r in enumerate(rows) if r[0] == default), 2)
    choice = IntPrompt.ask(
        f"\n[bold]{t('msg.pick_scope')}[/bold]",
        default=default_idx, choices=["1", "2", "3"],
        show_choices=False,
    )
    return rows[choice - 1][0]


def _ask_ipv6_pref(default_yes: bool) -> bool:
    """Prompt: should we register IPv6 DoH IPs too? Only if v6 actually works."""
    from ..detect.ipv6 import has_ipv6
    if not has_ipv6():
        console.print(f"[dim]{t('msg.ipv6.unavailable')} — {t('msg.ipv6_skip')}[/dim]")
        return False
    console.print(f"[green]{t('msg.ipv6.available')}[/green]")
    ans = Prompt.ask(
        f"[bold]{t('msg.set_ipv6')}[/bold]",
        choices=["y", "n"],
        default="y" if default_yes else "n",
    ).lower()
    return ans == "y"


def _force_doh_interactive(cfg: dict) -> dict:
    """Menu-side wrapper for force-doh: asks the user, then runs typer."""
    saved_scope = cfg.get("scope") or "country+majors"
    saved_ipv6 = cfg.get("set_ipv6", True)

    scope = _ask_scope(saved_scope)
    set_ipv6 = _ask_ipv6_pref(saved_ipv6)
    cfg = user_config.update(scope=scope, set_ipv6=set_ipv6)

    argv = ["force-doh", "--scope", scope]
    if not set_ipv6:
        argv.append("--no-ipv6")
    _run_typer(argv)
    return cfg


def _hosts_repair() -> None:
    from ..fix.hosts_repair import HOSTS_PATH, analyze, repair
    from ..utils import is_admin

    info = analyze(HOSTS_PATH)
    console.print(f"[cyan]{t('msg.hosts_analysed', total=info.total_lines, active=info.active_entries, issues=len(info.issues))}[/cyan]")
    for issue in info.issues[:30]:
        console.print(f"  L{issue.line_no} [{issue.kind}] {issue.detail}")
    if not info.issues:
        console.print(f"[green]✓ {t('msg.hosts_clean')}[/green]")
        return

    if Prompt.ask(t("msg.hosts_fix_confirm"),
                  choices=["y", "n"], default="n").lower() != "y":
        return
    if not is_admin():
        console.print(f"[red]{t('msg.need_admin')}[/red]")
        return
    kept, removed = repair(HOSTS_PATH)
    console.print(f"[green]✓ {t('msg.hosts_repaired', kept=kept, removed=removed)}[/green]")


def _outage_diagnose() -> None:
    from ..detect.outage import diagnose
    rep = diagnose()
    table = Table(title=t("label.outage_chain"), box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column(t("label.step"))
    table.add_column(t("label.result"))
    table.add_column(t("label.detail"), overflow="fold")
    for i, s in enumerate(rep.steps, 1):
        mark = "[green]✓[/green]" if s.ok else "[red]✗[/red]"
        table.add_row(str(i), s.name, mark, s.detail)
    console.print(table)
    if rep.failing_step:
        console.print(Panel(
            f"[bold]{t('label.summary')}: [/bold]{rep.summary}\n"
            f"[bold]{t('label.fix_hint')}: [/bold]{rep.fix_hint}",
            border_style="yellow", title="⚠"))
    else:
        console.print(f"[green]✓ {t('msg.outage_all_ok')}[/green]")


def _hijack_check() -> None:
    from ..detect.hijack import detect_hijack
    v = detect_hijack()
    if v.is_hijacked:
        console.print(Panel(
            f"[red]{t('msg.hijack_yes')}[/red]\n{v.reason}",
            border_style="red", title="⚠"))
    elif v.total_count == 0:
        console.print(Panel(
            f"[yellow]{t('msg.hijack_unknown')}[/yellow]\n{v.reason}",
            border_style="yellow"))
    else:
        console.print(Panel(
            f"[green]{t('msg.hijack_no')}[/green]\n{v.reason}",
            border_style="green"))


def dispatch(action: str, cfg: dict) -> dict:
    """Run one menu action; return the (possibly updated) config dict."""
    if action == "exit":
        raise SystemExit(0)
    if action == "switch_lang":
        new = ask_language(cfg.get("lang"))
        cfg = user_config.update(lang=new)
        set_lang(new)
        return cfg
    if action == "switch_country":
        new = ask_country(cfg.get("lang", "en"), cfg.get("country"))
        return user_config.update(country=new)
    if action in _TYPER_DELEGATES:
        _run_typer(_TYPER_DELEGATES[action])
        return cfg
    if action == "force_doh":
        return _force_doh_interactive(cfg)
    if action == "hosts_repair":
        _hosts_repair()
        return cfg
    if action == "outage_diagnose":
        _outage_diagnose()
        return cfg
    if action == "hijack_check":
        _hijack_check()
        return cfg
    return cfg
