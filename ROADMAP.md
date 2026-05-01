# NetMedic Roadmap

This file tracks deliberate, larger work that is **planned but not yet
implemented**. Items here are scaffolded in code (see the
``platform_adapter.py`` stubs for example) so the API shape stays
stable while the implementation lands incrementally.

If you want to help with one of these, please open a PR — or comment
on the linked issue when one exists.

## Cross-platform support

> Today: Windows-only. The framework hooks are already in place under
> ``netmedic/platform_adapter.py``.

- [ ] **macOS backend** (`MacOSPlatform`)
  - [ ] Active interface discovery via `scutil --dns` and
        `networksetup -listallnetworkservices`
  - [ ] DNS apply/reset via `networksetup -setdnsservers`
  - [ ] DNS flush via `dscacheutil -flushcache; killall -HUP mDNSResponder`
  - [ ] hosts at `/etc/hosts` (existing logic mostly portable)
  - [ ] No NRPT equivalent — split DNS via `/etc/resolver/<domain>`
        files instead
- [ ] **Linux backend** (`LinuxPlatform`)
  - [ ] Detect resolver stack (systemd-resolved / NetworkManager /
        plain `/etc/resolv.conf`)
  - [ ] DNS apply via `resolvectl dns <iface> <ips>` or `nmcli`
  - [ ] DNS flush via `resolvectl flush-caches` or service restart
  - [ ] hosts at `/etc/hosts`
  - [ ] Split DNS via systemd-resolved per-link DNS

## Richer ipconfig output

> Today: NetMedic exposes `status` (active adapter + NRPT). It does
> NOT yet replicate the depth of `ipconfig /all`.

- [ ] **`network_snapshot()` API** on `PlatformAdapter`
  - [ ] All adapters (not just default-route), with up/down state
  - [ ] MAC address, link speed
  - [ ] DHCP server, lease obtained/expires, DHCP client ID
  - [ ] DNS suffix list, NetBIOS over TCP/IP state
  - [ ] IPv6: SLAAC prefixes, temporary addresses, scope IDs
  - [ ] Routing table summary (default + on-link)
  - [ ] WINS servers (yes, still relevant in some enterprises)
  - [ ] VPN tunnel detection
- [ ] **`status --verbose`** menu item to render the snapshot

## DNS scope & IPv6 polish

- [x] 3-way scope selector (country / country+majors / all)
- [x] Interactive prompt to register IPv6 DoH IPs only when v6 works
- [ ] Per-region "smart" scope: detect ASN of exit IP and suggest a
      preset (e.g. AS2914 → JP exit → prefer Quad101 / IIJ / Cloudflare)
- [ ] Custom user-added providers in `~/.netmedic/providers.json`

## Localization completeness

- [x] Menu / label / wizard / scope keys in EN + zh-CN
- [ ] Translate the new scope/IPv6 keys into zh-TW, ja, ko, ru
- [ ] Translate provider `notes` strings (currently English only)
- [ ] Add `pt-BR`, `de`, `fr`, `es`, `vi` locale stubs

## Diagnostic depth

- [ ] DNSSEC validation check per resolver
- [ ] ECS (EDNS Client Subnet) opt-out detection
- [ ] DoT alongside DoH (port 853 fallback when 443 is blocked)
- [ ] Local DoH proxy mode (long-running daemon on 127.0.0.1:53 for
      machines that can't enable system-level DoH)

## Telemetry policy

> NetMedic will never call home. Period. This section exists only so
> contributors know what's off the table.

- [ ] Opt-in **anonymous** speed/pollution submission to a public
      dataset (CSV uploaded with explicit user consent per submission)
- [ ] Self-hosted backend reference (no third-party services)

---

Last updated: 2026-05-01
