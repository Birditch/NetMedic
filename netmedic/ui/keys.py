"""Cross-platform non-blocking single-key reader.

Used by the Live-rendered main menu so we can poll the keyboard while
Rich keeps redrawing the screen at ~8 fps. Redraws automatically pick
up terminal-size changes, which is what gives us window resize support.
"""
from __future__ import annotations
import contextlib
import os
import sys


_IS_POSIX = os.name != "nt"


@contextlib.contextmanager
def cbreak_mode():
    """Switch stdin to cbreak (no canonical, no echo) on POSIX systems.

    No-op on Windows — ``msvcrt`` already gives us per-key reads.
    """
    if not _IS_POSIX:
        yield
        return
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd, termios.TCSANOW)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def getch_nowait() -> str | None:
    """Return a single character if one is queued, else ``None``.

    Never blocks. ``cbreak_mode`` must be active on POSIX for this to
    work as expected.
    """
    if not _IS_POSIX:
        try:
            import msvcrt
        except ImportError:
            return None
        if not msvcrt.kbhit():
            return None
        try:
            return msvcrt.getwch()
        except Exception:  # noqa: BLE001
            return None
    import select
    ready, _, _ = select.select([sys.stdin], [], [], 0)
    if not ready:
        return None
    return sys.stdin.read(1)
