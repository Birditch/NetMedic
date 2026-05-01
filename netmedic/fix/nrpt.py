"""Manage Windows NRPT (Name Resolution Policy Table) rules.

NRPT lets the OS pick a DNS server based on the queried namespace, so we use
it to implement split-horizon DNS:

    *.qq.com / *.taobao.com / ... -> AliDNS / DNSPod
    everything else                 -> default (Cloudflare/Google/...)

Every rule we create is tagged with ``[NetMedic]`` in the Comment field so
``restore`` can clean up only its own rules and leave any user/IT-pushed
policies alone.
"""
from __future__ import annotations
import json

from ..utils import run_powershell

NRPT_COMMENT_TAG = "[NetMedic]"


def list_rules() -> list[dict]:
    # ``Get-DnsClientNrptRule`` returns ``NameServers`` as
    # ``System.Net.IPAddress`` objects. ``ConvertTo-Json`` serializes
    # those as the underlying CIM dict (``{Address: 84215263, ...}``)
    # which is unreadable. Explicitly project to the dotted-quad string
    # via ``IPAddressToString`` so the JSON we round-trip is plain text.
    rc, out, _ = run_powershell(
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
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return [data]
    return data


def add_rules(namespaces: list[str], servers: list[str]) -> int:
    """Add an NRPT rule per namespace tagged with ``[NetMedic]``.

    Returns the count successfully created. Ignores duplicates / individual
    failures so partial application doesn't blow up the whole apply step.
    """
    if not namespaces or not servers:
        return 0
    quoted_servers = ",".join(f'"{s}"' for s in servers)
    quoted_namespaces = ",".join(f'".{n.lstrip(".")}"' for n in namespaces)
    script = f"""
$ns = @({quoted_namespaces})
$srv = @({quoted_servers})
$ok = 0
foreach ($n in $ns) {{
    try {{
        Add-DnsClientNrptRule -Namespace $n -NameServers $srv -Comment '{NRPT_COMMENT_TAG}' -ErrorAction Stop | Out-Null
        $ok++
    }} catch {{ }}
}}
$ok
"""
    rc, out, err = run_powershell(script, timeout=180)
    if rc != 0:
        raise RuntimeError(f"add_rules 失败: {err.strip() or out.strip()}")
    last_line = out.strip().splitlines()[-1] if out.strip() else "0"
    try:
        return int(last_line)
    except ValueError:
        return 0


def remove_our_rules() -> int:
    """Remove every NRPT rule whose Comment matches NetMedic's tag."""
    script = f"""
$rules = Get-DnsClientNrptRule | Where-Object {{ $_.Comment -eq '{NRPT_COMMENT_TAG}' }}
$count = 0
foreach ($r in $rules) {{
    try {{
        Remove-DnsClientNrptRule -Name $r.Name -Force -ErrorAction Stop
        $count++
    }} catch {{ }}
}}
$count
"""
    rc, out, _ = run_powershell(script, timeout=180)
    if rc != 0:
        return 0
    last_line = out.strip().splitlines()[-1] if out.strip() else "0"
    try:
        return int(last_line)
    except ValueError:
        return 0
