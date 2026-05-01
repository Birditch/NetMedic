"""MTU sanity check.

We don't binary-search the path MTU (slow, fragile across firewalls). We just
read the configured MTU on each connected adapter and flag obvious anomalies.
"""
from __future__ import annotations
import json
from dataclasses import dataclass

from ..config import MTU_FLOOR, MTU_NORMAL
from ..utils import run_powershell


@dataclass
class MtuInfo:
    interface: str
    current_mtu: int
    notes: str


def get_interface_mtus() -> list[tuple[str, int]]:
    rc, out, _ = run_powershell(
        "Get-NetIPInterface -AddressFamily IPv4 -ConnectionState Connected | "
        "Select-Object InterfaceAlias, NlMtu | ConvertTo-Json -Compress"
    )
    if rc != 0 or not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return [(d.get("InterfaceAlias", "?"), int(d.get("NlMtu", 0))) for d in data]


def analyze_mtu() -> list[MtuInfo]:
    infos: list[MtuInfo] = []
    for name, mtu in get_interface_mtus():
        if name in {"Loopback Pseudo-Interface 1"}:
            continue
        if mtu == 0:
            note = "未知 / 接口已禁用"
        elif mtu < MTU_FLOOR:
            note = "异常偏低, 严重影响吞吐"
        elif mtu < 1400:
            note = "偏低, 可能是 PPPoE / VPN 隧道"
        elif mtu == MTU_NORMAL:
            note = "标准以太网 MTU"
        elif mtu > MTU_NORMAL:
            note = "巨型帧, 路径需全程支持否则会丢包"
        else:
            note = "正常区间"
        infos.append(MtuInfo(name, mtu, note))
    return infos
