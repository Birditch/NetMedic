"""Flush the Windows DNS resolver cache."""
from __future__ import annotations
import subprocess


def flush_dns() -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["ipconfig", "/flushdns"], capture_output=True, timeout=15
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return 1, f"flush failed: {exc!r}"
    return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", errors="replace")
