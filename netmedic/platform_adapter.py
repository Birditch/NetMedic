"""Cross-platform OS abstraction.

NetMedic was Windows-first, but the diagnostic surface (adapter info,
DNS apply/restore, hosts, MTU, ipconfig-equivalent) is conceptually OS-
agnostic. This module is the seam where future macOS / Linux backends
plug in. Today only Windows is fully wired; macOS and Linux raise
``NotImplementedError`` with a pointer to the roadmap.

Architecture:

    PlatformAdapter             # abstract base
    ├── WindowsPlatform         # full implementation
    ├── MacOSPlatform           # TODO — see ROADMAP.md
    └── LinuxPlatform           # TODO — see ROADMAP.md

Call ``current()`` to get the right implementation for the running OS.
The shipped Windows commands continue to live in ``netmedic.detect.*``
and ``netmedic.fix.*`` and are simply re-exported through
``WindowsPlatform`` so existing call sites can migrate incrementally.
"""
from __future__ import annotations
import sys
from typing import Any

ROADMAP_URL = "https://github.com/Birditch/NetMedic/blob/main/ROADMAP.md"


class PlatformAdapter:
    """Abstract OS adapter — every backend implements this surface."""

    name: str = "abstract"

    # --- discovery ----------------------------------------------------
    def get_active_adapter(self) -> Any:
        raise NotImplementedError

    def list_dns_servers(self, iface: Any) -> list[str]:
        raise NotImplementedError

    # --- mutation -----------------------------------------------------
    def set_dns(self, iface: Any, servers: list[str]) -> None:
        raise NotImplementedError

    def reset_dns(self, iface: Any) -> None:
        raise NotImplementedError

    def flush_dns(self) -> tuple[int, str]:
        raise NotImplementedError

    # --- privilege ----------------------------------------------------
    def is_admin(self) -> bool:
        raise NotImplementedError

    # --- TODO surface (richer ipconfig output) ------------------------
    def network_snapshot(self) -> dict:
        """Return a rich, structured equivalent of `ipconfig /all`.

        TODO(roadmap): collect MAC, lease times, DHCP server, IPv6 SLAAC
        prefixes, NetBIOS state, DNS suffixes, WINS, gateway metrics,
        VPN tunnels — see ROADMAP.md "richer ipconfig" item.
        """
        raise NotImplementedError(
            f"network_snapshot() not implemented yet — see {ROADMAP_URL}"
        )


class WindowsPlatform(PlatformAdapter):
    name = "windows"

    def get_active_adapter(self):
        from .detect.adapter import get_active_adapter
        return get_active_adapter()

    def list_dns_servers(self, iface):
        if iface is None:
            return []
        return list(iface.dns_servers)

    def set_dns(self, iface, servers):
        from .fix.dns_apply import set_dns
        set_dns(iface.ifindex, servers)

    def reset_dns(self, iface):
        from .fix.dns_apply import reset_dns
        reset_dns(iface.ifindex)

    def flush_dns(self):
        from .fix.flush import flush_dns
        return flush_dns()

    def is_admin(self):
        from .utils import is_admin
        return is_admin()


class MacOSPlatform(PlatformAdapter):
    """macOS support is on the roadmap."""

    name = "darwin"

    def _todo(self) -> "NotImplementedError":
        # TODO(roadmap): use `scutil --dns`, `networksetup -setdnsservers`,
        # `networksetup -listallnetworkservices` for the moving parts.
        return NotImplementedError(
            f"macOS support is planned. Track at {ROADMAP_URL}"
        )

    def get_active_adapter(self): raise self._todo()
    def list_dns_servers(self, iface): raise self._todo()
    def set_dns(self, iface, servers): raise self._todo()
    def reset_dns(self, iface): raise self._todo()
    def flush_dns(self): raise self._todo()
    def is_admin(self):
        import os
        return os.geteuid() == 0


class LinuxPlatform(PlatformAdapter):
    """Linux support is on the roadmap."""

    name = "linux"

    def _todo(self) -> "NotImplementedError":
        # TODO(roadmap): split between systemd-resolved (resolvectl),
        # NetworkManager (nmcli), and plain /etc/resolv.conf rewriting.
        return NotImplementedError(
            f"Linux support is planned. Track at {ROADMAP_URL}"
        )

    def get_active_adapter(self): raise self._todo()
    def list_dns_servers(self, iface): raise self._todo()
    def set_dns(self, iface, servers): raise self._todo()
    def reset_dns(self, iface): raise self._todo()
    def flush_dns(self): raise self._todo()
    def is_admin(self):
        import os
        return os.geteuid() == 0


def current() -> PlatformAdapter:
    """Return the adapter that matches the running interpreter's OS."""
    if sys.platform.startswith("win"):
        return WindowsPlatform()
    if sys.platform == "darwin":
        return MacOSPlatform()
    return LinuxPlatform()
