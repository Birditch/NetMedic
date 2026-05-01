"""NetMedic launcher.

Two responsibilities, in order:

1. **Dependency bootstrap.** Rich / typer / dnspython etc. may not be
   installed yet. We try to import Rich up front: when it's already
   present (re-execs after install, or installs done out-of-band), the
   bootstrap dialog itself is rendered in Rich. When it isn't, we fall
   back to stdlib ``print`` / ``input`` for that one screen only —
   the rest of NetMedic still uses Rich exclusively. After a
   successful install we ``os.execv`` ourselves so the freshly
   installed wheels are discoverable on ``sys.path``.

2. **Hand off to the interactive launcher.** Once dependencies are in
   place, we import ``netmedic.launcher`` and call ``run(argv)``.
   Direct CLI usage (``python run.py force-doh``, etc.) still works —
   the launcher forwards everything after the menu to the typer app.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys

# (import-name, pip-name) — pip-name may differ for namespaced packages.
REQUIRED: list[tuple[str, str]] = [
    ("dns",   "dnspython>=2.8"),
    ("rich",  "rich>=14.0"),
    ("typer", "typer>=0.15"),
    ("httpx", "httpx>=0.28"),
    ("h2",    "h2>=4.3"),
]


def _find_missing() -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for import_name, pip_name in REQUIRED:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append((import_name, pip_name))
    return missing


# --- Rich-aware UI helpers ---------------------------------------------
# We only use Rich here if it's already importable; otherwise we fall
# back to stdlib so the *very first* run on a fresh interpreter still
# has a usable prompt.

def _try_rich():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm
        from rich.table import Table
        from rich import box
        return Console(), Panel, Confirm, Table, box
    except Exception:  # noqa: BLE001
        return None


def _show_missing(missing: list[tuple[str, str]]) -> None:
    rich = _try_rich()
    if rich is None:
        print("=" * 64)
        print("  NetMedic — Missing Python dependencies detected")
        print("=" * 64)
        for _, pip_name in missing:
            print(f"  - {pip_name}")
        print("-" * 64)
        return
    console, Panel, _Confirm, Table, box = rich
    table = Table(box=box.SIMPLE_HEAD, expand=True)
    table.add_column("Package", style="bold cyan")
    table.add_column("Required version", style="dim")
    for import_name, pip_name in missing:
        if ">=" in pip_name:
            name, _, ver = pip_name.partition(">=")
            table.add_row(name, ">= " + ver)
        else:
            table.add_row(pip_name, "")
    console.print(Panel(
        table,
        title="[bold yellow]NetMedic — Missing Python dependencies[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))


def _confirm_install() -> bool:
    rich = _try_rich()
    if rich is None:
        try:
            ans = input("Install them now via pip? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return ans in ("", "y", "yes", "是")
    _console, _Panel, Confirm, _Table, _box = rich
    try:
        return Confirm.ask("Install them now via pip?", default=True)
    except (EOFError, KeyboardInterrupt):
        return False


def _say(text: str, *, style: str = "") -> None:
    rich = _try_rich()
    if rich is None:
        print(text)
        return
    console = rich[0]
    if style:
        console.print(text, style=style)
    else:
        console.print(text)


def _bootstrap() -> None:
    missing = _find_missing()
    if not missing:
        return
    _show_missing(missing)
    if not _confirm_install():
        _say("Cannot continue without dependencies. Exiting.", style="red")
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           *(p for _, p in missing)]
    _say(f"\n[dim]>>> {' '.join(cmd)}[/dim]\n")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        _say("\nInstall failed. Please install the listed packages "
             "manually and run NetMedic again.", style="red")
        sys.exit(rc)
    _say("\n[green]✓ Install complete.[/green] "
         "[dim]Restarting NetMedic with the new packages…[/dim]\n")
    # Replace this Python process so the freshly-installed wheels are
    # discoverable on sys.path without a stale interpreter cache.
    os.execv(sys.executable, [sys.executable, *sys.argv])


def main() -> None:
    _bootstrap()
    # Safe to import third-party from here on.
    from netmedic.launcher import run
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
