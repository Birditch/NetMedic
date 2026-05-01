"""Manage a NetMedic-owned block inside the Windows hosts file.

We never touch lines outside the marker block, so user-added entries are
preserved.
"""
from __future__ import annotations
from pathlib import Path

HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
BEGIN = "# >>> NetMedic >>>"
END = "# <<< NetMedic <<<"


def read_hosts() -> str:
    return HOSTS_PATH.read_text(encoding="utf-8", errors="replace")


def write_hosts(content: str) -> None:
    HOSTS_PATH.write_text(content, encoding="utf-8")


def replace_block(entries: list[tuple[str, str]]) -> None:
    """Replace the NetMedic block in hosts with the given (ip, hostname) list."""
    if not entries:
        remove_block()
        return
    body = "\n".join(f"{ip}\t{host}" for ip, host in entries)
    block = f"{BEGIN}\n{body}\n{END}"
    text = read_hosts()
    if BEGIN in text and END in text:
        head, _, rest = text.partition(BEGIN)
        _, _, tail = rest.partition(END)
        new = head.rstrip() + ("\n\n" if head.strip() else "") + block + "\n" + tail.lstrip()
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
    write_hosts(new)


def remove_block() -> bool:
    text = read_hosts()
    if BEGIN not in text or END not in text:
        return False
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    new = head.rstrip() + "\n" + tail.lstrip()
    write_hosts(new)
    return True
