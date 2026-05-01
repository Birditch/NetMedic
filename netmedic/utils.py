"""Common helpers: privilege checks, subprocess wrappers, paths."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Project source root (used only for legacy / test discovery).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# User-data directories. Honours ``NETMEDIC_HOME`` so power users can
# pin the state to a specific drive / share. Defaults to
# ``%USERPROFILE%\.netmedic`` on Windows and ``$HOME/.netmedic`` on
# POSIX, so the data is writable after a ``pip install`` into a
# non-writable site-packages.
def _data_dir() -> Path:
    override = os.environ.get("NETMEDIC_HOME")
    if override:
        return Path(override)
    return Path.home() / ".netmedic"


BACKUP_DIR = _data_dir() / "backups"
LOG_DIR = _data_dir() / "logs"

_PS_PRELUDE = (
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    "$OutputEncoding=[Text.Encoding]::UTF8;"
    "$ProgressPreference='SilentlyContinue';"
)


def is_admin() -> bool:
    """True if the current process has the elevated privileges that the
    ``apply`` / ``restore`` / ``force-doh`` commands need.

    - Windows: ``shell32.IsUserAnAdmin``.
    - POSIX (macOS / Linux): effective UID is 0.
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes  # imported lazily so non-Windows imports stay clean
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:  # noqa: BLE001
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def run_powershell(script: str, timeout: int = 30) -> tuple[int, str, str]:
    """Run a PowerShell snippet, return (returncode, stdout, stderr) as UTF-8 text."""
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-Command", _PS_PRELUDE + script,
        ],
        capture_output=True,
        timeout=timeout,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    return completed.returncode, stdout, stderr


def run_cmd(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run a regular command, decode bytes as UTF-8 with replace fallback."""
    completed = subprocess.run(args, capture_output=True, timeout=timeout)
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    return completed.returncode, stdout, stderr
