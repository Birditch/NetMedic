# Changelog

All notable changes to NetMedic will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-01

First public release.

### Added

- **Interactive Rich-rendered launcher** (`python run.py` with no args).
  First-run wizard asks for UI language and country/region; subsequent
  runs reuse the saved choice (Enter accepts current).
- **Auto dependency bootstrap.** If `dnspython / rich / typer / httpx /
  h2` are missing, `run.py` prompts, pip-installs, and re-execs itself.
- **14-item numbered menu** with localized name + summary + admin
  badge per item.
- **Country / region presets** (`netmedic/data/countries.py`):
  AUTO, CN, JP, TW, HK, KR, US, EU, RU, SG.
- **DoH scope selector** (`country` / `country+majors` / `all`) with
  persistent default in user config.
- **IPv6 DoH consent prompt** when v6 is reachable — gives the user a
  chance to skip even when v6 works.
- **Router DNS hijack detector** (`netmedic/detect/hijack.py`).
- **Five-layer outage diagnosis chain** (`netmedic/detect/outage.py`)
  — Loopback → Gateway → Internet → DNS → HTTPS.
- **hosts file repair** (`netmedic/fix/hosts_repair.py`) — duplicate /
  blackhole / malformed cleanup that respects marker blocks.
- **Cross-platform abstraction stub** (`platform_adapter.py`) —
  Windows fully wired, macOS / Linux planned (see ROADMAP.md).
- **More uncensored DoH providers**: ControlD (free unfiltered),
  Mullvad encrypted-only, DNS.WATCH (DE), Vercara UltraDNS,
  DNS.SB, BaiduDNS (v6), CFIEC IPv6-only, Yandex (RU).
- **Multilingual READMEs**: `README.md` (English default),
  `README-zh-CN.md`, `README-zh-TW.md`, with cross-language switcher.
- **Locale files** extended with menu / feature / wizard strings for
  all six supported languages (zh-TW / ja / ko / ru pending the new
  scope+IPv6 keys — tracked in ROADMAP.md).
- **`--scope` CLI flag** on `force-doh` for scripting.
- **Persistent user config** at `.netmedic_config.json` now stores
  language, country, scope, and IPv6 preference.
- **ROADMAP.md** publishing planned cross-platform, ipconfig, and
  diagnostic-depth work.

### Changed

- IPv6 DoH IPs verified against the curated 2026-05-01 dataset
  (Quad9 v6 corrected, AdGuard v6 updated to `:ad1:ff`).
- **Minimum Python version raised to 3.10** (driven by dnspython 2.8 and
  typer 0.25 — both require 3.10+).
- **CI bumped to latest LTS actions**: `actions/checkout@v6` (Node 24
  native) and `actions/setup-python@v6` (Node 24 native).
- **CI matrix expanded** to Python 3.10 / 3.11 / 3.12 / 3.13.
- `launcher.py` split into single-responsibility files under
  `netmedic/ui/` (`widgets`, `wizard`, `menu`, `actions`).
- pyflakes is enforced in CI.

### Notes

NetMedic is built with **JetBrains PyCharm** (under their Open Source
Development License program), **Anthropic Claude Code**, and
**OpenAI Codex**. See README for full credits.
