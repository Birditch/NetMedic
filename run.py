"""NetMedic launcher.

Two responsibilities, in order:

1. **Dependency bootstrap.** Rich / typer / dnspython etc. may not be
   installed yet, so this file uses *only the standard library* until it
   has confirmed every required third-party package is importable.
   Missing packages trigger a y/n prompt; if the user agrees, we run
   ``pip install --upgrade`` and then ``os.execv`` ourselves to start
   over with the freshly installed packages on ``sys.path``.

2. **Hand off to the interactive launcher.** Once dependencies are in
   place, we import ``netmedic.launcher`` and call ``main(argv)``. The
   launcher does first-run language / country selection, persists the
   choice, and then drives the numbered menu. Direct-CLI usage
   (``python run.py force-doh``, etc.) still works — the launcher
   forwards everything after the menu to the typer app.
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


def _ask(prompt: str) -> bool:
    try:
        ans = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans in ("", "y", "yes", "是")


def _bootstrap() -> None:
    missing = _find_missing()
    if not missing:
        return

    print("=" * 64)
    print("  NetMedic — Missing Python dependencies detected")
    print("=" * 64)
    for _, pip_name in missing:
        print(f"  - {pip_name}")
    print("-" * 64)
    if not _ask("Install them now via pip? [Y/n] "):
        print("Cannot continue without dependencies. Exiting.")
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade",
           *(p for _, p in missing)]
    print(f"\n>>> {' '.join(cmd)}\n")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print("\nInstall failed. Please install the listed packages "
              "manually and run NetMedic again.")
        sys.exit(rc)
    print("\nInstall complete. Restarting NetMedic with the new packages...\n")
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
