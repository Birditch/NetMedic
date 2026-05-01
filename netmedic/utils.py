"""Common helpers: privilege checks, subprocess wrappers, paths."""
from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
LOG_DIR = PROJECT_ROOT / "logs"

_PS_PRELUDE = (
    "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    "$OutputEncoding=[Text.Encoding]::UTF8;"
    "$ProgressPreference='SilentlyContinue';"
)


def is_admin() -> bool:
    """True if the current process is elevated (Windows administrator)."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
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
