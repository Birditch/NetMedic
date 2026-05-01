"""Backup current DNS / NRPT settings before mutating anything."""
from __future__ import annotations
import json
import time
from pathlib import Path

from ..utils import BACKUP_DIR, run_powershell


def backup_dns(ifindex: int) -> Path:
    """Snapshot the adapter's DNS settings + all NRPT rules to ``backups/``.

    Returns the path of the per-run backup; ``backups/latest.json`` is also
    refreshed so ``restore`` can find the most recent state easily.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    rc, out, err = run_powershell(
        f"Get-DnsClientServerAddress -InterfaceIndex {ifindex} | "
        f"Select-Object InterfaceIndex, InterfaceAlias, AddressFamily, ServerAddresses | "
        f"ConvertTo-Json -Compress -Depth 4"
    )
    if rc != 0:
        raise RuntimeError(f"备份网卡 DNS 失败: {err.strip() or out.strip()}")
    dns_json = out.strip()

    rc2, nrpt_out, _ = run_powershell(
        "Get-DnsClientNrptRule | ForEach-Object { "
        "[PSCustomObject]@{ "
        "Name = $_.Name; "
        "Namespace = @($_.Namespace); "
        "NameServers = @($_.NameServers | ForEach-Object { "
        "    if ($_ -is [string]) { $_ } else { $_.IPAddressToString } "
        "}); "
        "Comment = $_.Comment "
        "} } | ConvertTo-Json -Compress -Depth 4"
    )

    payload = {
        "timestamp": time.time(),
        "ifindex": ifindex,
        "dns": json.loads(dns_json) if dns_json else None,
        "nrpt": json.loads(nrpt_out) if (rc2 == 0 and nrpt_out.strip()) else None,
    }
    p = BACKUP_DIR / f"backup-{int(time.time())}.json"
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (BACKUP_DIR / "latest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


def latest_backup() -> dict | None:
    p = BACKUP_DIR / "latest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
