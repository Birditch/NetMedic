"""Validate and repair the Windows hosts file.

What this does:
- Detect duplicate hostname entries (multiple IPs for the same host).
- Detect entries pointing to obviously wrong IPs (0.0.0.0, 127.0.0.1
  for non-localhost names — common ad-blocker leftovers).
- Detect malformed lines.
- Optionally write back a cleaned version, preserving everything we
  don't recognize as broken.

We never touch lines inside another tool's marker block (e.g.
``# >>> NetMedic >>>``) — those are owned by something else.
"""
from __future__ import annotations
import ipaddress
from dataclasses import dataclass, field
from pathlib import Path

HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")


@dataclass
class HostsIssue:
    line_no: int
    line: str
    kind: str
    detail: str


@dataclass
class HostsAnalysis:
    total_lines: int
    active_entries: int
    issues: list[HostsIssue] = field(default_factory=list)


def _is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def analyze(path: Path = HOSTS_PATH) -> HostsAnalysis:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    issues: list[HostsIssue] = []
    seen: dict[str, list[tuple[int, str]]] = {}
    active = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            issues.append(HostsIssue(i, line, "malformed",
                                     "expected '<ip> <hostname>'"))
            continue
        ip, *hosts = parts
        if not _is_ip(ip):
            issues.append(HostsIssue(i, line, "malformed",
                                     f"first token '{ip}' is not an IP"))
            continue
        for h in hosts:
            if h.startswith("#"):
                break
            active += 1
            seen.setdefault(h.lower(), []).append((i, ip))
            # Suspicious: blocking entry for a non-localhost host
            if ip in {"0.0.0.0", "127.0.0.1", "::1"} and h.lower() not in {
                    "localhost", "localhost.localdomain", "broadcasthost"}:
                issues.append(HostsIssue(i, line, "blackhole",
                                         f"{h} -> {ip} (likely ad-blocker)"))

    for host, occ in seen.items():
        if len(occ) > 1:
            ips = ", ".join(f"L{ln}={ip}" for ln, ip in occ)
            issues.append(HostsIssue(occ[0][0],
                                     "(multiple lines)",
                                     "duplicate",
                                     f"{host} appears {len(occ)} times: {ips}"))

    return HostsAnalysis(len(lines), active, issues)


def repair(path: Path = HOSTS_PATH,
           drop_blackholes: bool = True,
           drop_duplicates: bool = True) -> tuple[int, int]:
    """Rewrite the hosts file with detected issues fixed.

    Returns (entries_kept, entries_removed). Lines we don't understand
    (comments, blank, marker blocks, malformed-but-not-blackhole) are
    preserved verbatim.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    seen_hosts: set[str] = set()
    kept: list[str] = []
    removed = 0
    in_marker_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# >>>") and stripped.endswith(">>>"):
            in_marker_block = True
            kept.append(line)
            continue
        if stripped.startswith("# <<<") and stripped.endswith("<<<"):
            in_marker_block = False
            kept.append(line)
            continue
        if in_marker_block or not stripped or stripped.startswith("#"):
            kept.append(line)
            continue

        parts = stripped.split()
        if len(parts) < 2 or not _is_ip(parts[0]):
            kept.append(line)
            continue

        ip = parts[0]
        hosts = []
        for h in parts[1:]:
            if h.startswith("#"):
                break
            hosts.append(h)

        if drop_blackholes and ip in {"0.0.0.0", "127.0.0.1", "::1"}:
            non_local = [h for h in hosts
                         if h.lower() not in {"localhost",
                                              "localhost.localdomain",
                                              "broadcasthost"}]
            if non_local:
                removed += 1
                continue

        if drop_duplicates:
            unique = [h for h in hosts if h.lower() not in seen_hosts]
            if not unique:
                removed += 1
                continue
            for h in unique:
                seen_hosts.add(h.lower())
            kept.append(f"{ip}\t{' '.join(unique)}")
        else:
            kept.append(line)

    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return len(kept), removed
