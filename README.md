<!--
   NetMedic - Windows DNS & connectivity doctor
   Author: Birditch  |  License: MIT  |  Version: 1.0.0
   Keywords: Windows DNS repair, DoH (DNS over HTTPS), encrypted DNS,
             split-horizon DNS, NRPT, soft-router diagnosis, dnspython,
             cross-region DNS routing
-->

# NetMedic — Windows DNS / Network Doctor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](netmedic/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](#requirements)
[![CI](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml/badge.svg)](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Birditch/NetMedic?style=social)](https://github.com/Birditch/NetMedic/stargazers)

> **Detect and repair DNS / connectivity issues on Windows. First-class
> support for "asymmetric-exit" home networks (a soft router that sends
> some traffic through a foreign exit while keeping the rest local) where
> naive DNS configs cause subtle slowness, broken third-party logins, and
> region-mismatched routing.**

**Platform status**: Windows-only today. **Linux** and **macOS** support is
on the [ROADMAP](ROADMAP.md) — the cross-platform abstraction is already
scaffolded under `netmedic/platform_adapter.py`, and backends will land
incrementally.

**Languages**: **English** · [简体中文](README-zh-CN.md) · [繁體中文](README-zh-TW.md)

---

## Sponsor

Stable, affordable network access goes a long way toward reproducing the
problems NetMedic was built to diagnose. The project is sponsored by
**[Pierlink](https://pierlink.net)** — quality, low-cost, reliable
network service. **Sign-up gets a 30-day trial** so you can compare
your own measurements before and after.

> *Pierlink keeps the lights on for the maintainer; it's not a
> dependency of NetMedic itself, just a recommended way to get a
> well-behaved network path for testing.*

---

## Why NetMedic exists

A typical pain pattern: traffic exits through a foreign node via a soft
router (OpenWrt / iKuai / Padavan / ...). Most things work, but:

- Some overseas web pages load slowly, then "magically" work after a
  refresh.
- Third-party single-sign-on flows for popular regional accounts can't
  detect an already-signed-in session in the official client.
- Some popular domestic services occasionally get sent through the slow
  foreign-exit path instead of staying on the local route.
- DNS leaks quietly bypass your privacy settings.

The root cause is almost always one of:

- **DNS poisoning at UDP/53** — packets are intercepted on the path and
  forged responses race the legitimate one.
- **Soft-router DNS hijacking** — every port-53 query is forced through
  a local resolver even when you've changed Windows DNS settings.
- **Wrong-region DNS answers** — domestic services get pointed at
  foreign-edge IPs, so they go out the foreign exit and trigger
  region-mismatch slowdowns or platform-side risk control.

NetMedic measures which of these you're actually hit by and offers
honest fixes — including using **Windows 11 native DoH (HTTPS:443)** to
bypass port-53 interception entirely.

## Features

- **Interactive launcher** — first-run wizard picks language and country,
  then drives a numbered Rich-rendered menu. Each menu item shows a
  localized description and whether admin is required before running.
- **Auto dependency bootstrap** — missing pip packages? You get prompted,
  installed, and the launcher transparently restarts.
- **Full network checkup** — adapter info, ping/loss vs. domestic +
  foreign hosts, MTU sanity.
- **Public DNS speed ranking** — UDP latency benchmark.
- **DNS pollution detection** — known poison-IP table + sub-floor
  latency heuristic.
- **DoH speed + pollution benchmark** — real HTTPS:443 measurements that
  cannot be faked by a port-53 hijack.
- **Scope selector** — pick *country only* / *country + global majors*
  / *all providers* before benchmarking.
- **Top-5 picker** — choose among the fastest *clean* DoH providers,
  with provider / operator / region / IPs / notes.
- **Smart split DNS** — region-sensitive namespaces always resolve via a
  region-appropriate DoH, written through Windows-native NRPT.
- **IPv6-aware** — auto-detects v6 connectivity and asks for explicit
  consent before registering v6 DoH IPs.
- **Atomic backup + one-click restore** — every `apply` snapshots prior
  DNS state to `backups/latest.json`; `restore` puts it back.
- **Hosts file repair** — duplicate / blackhole / malformed entry
  detection and cleanup, never touching marker blocks owned by other
  tools.
- **Outage diagnosis chain** — Loopback → Gateway → Internet → DNS →
  HTTPS, stop at the first failure and tell you exactly where it broke.
- **Router DNS hijack detector** — sub-5 ms responses from foreign DNS
  are a giveaway; NetMedic calls it out and recommends Force-DoH.
- **Multilingual UI** — 6 languages: 简体中文, 繁體中文, English,
  日本語, 한국어, Русский.

## Requirements

| Component | Version |
|---|---|
| Operating system | **Windows 10 / 11** today. Linux / macOS planned — see [ROADMAP](ROADMAP.md). |
| Python | **3.10+** (driven by dnspython 2.8 and typer 0.25) |
| Privileges | Administrator for `apply`, `restore`, `force-doh`, `hosts-fix` |

Dependencies always pulled at their latest compatible release in CI:
[dnspython](https://www.dnspython.org/) (with [httpx](https://www.python-httpx.org/) +
[h2](https://github.com/python-hyper/h2) for DoH),
[rich](https://github.com/Textualize/rich),
[typer](https://typer.tiangolo.com/).

## Install & first run

```powershell
git clone https://github.com/Birditch/NetMedic.git
cd NetMedic
python run.py
```

That's it. On the very first run NetMedic:

1. Detects whether `dnspython / rich / typer / httpx / h2` are
   importable. If any are missing, you get a yes/no prompt and pip
   installs them, after which the launcher restarts itself.
2. Asks for **UI language** (Enter keeps the suggested default).
3. Asks for **country / region** (Enter keeps `AUTO`).
4. Drops you into the numbered menu.

On subsequent runs, the saved choice is reused — but the menu always
has "Switch language" and "Switch country" at the top so you can
change either at any time, with Enter accepting the current value.

## Usage modes

- **Interactive menu** — `python run.py` (no arguments) → numbered menu.
- **Direct CLI** — every menu action is also exposed as a typer
  subcommand for scripting:

  ```powershell
  python run.py status
  python run.py force-doh
  python run.py force-doh --scope country+majors
  python run.py force-doh --intl-dns 1.1.1.1,8.8.8.8
  python run.py restore
  python run.py --lang ja check
  ```

## How NetMedic chooses "best DNS"

```
1. UDP DNS speed bench  → average / median / success%
2. Pollution score      → known poison IPs, sub-floor RTT (< 5 ms)
3. DoH HTTPS bench      → ground truth (router-proof)
4. Filter clean         → drop polluted / suspicious / timeout
5. Sort by avg latency  → present top 5 with operator + region + v4/v6 IPs
6. User picks           → register DoH templates, set DNS, write NRPT
```

## Internationalization

Locale files in [`locales/`](locales/) — one JSON per language:
[`en`](locales/en.json), [`zh-CN`](locales/zh-CN.json),
[`zh-TW`](locales/zh-TW.json), [`ja`](locales/ja.json),
[`ko`](locales/ko.json), [`ru`](locales/ru.json).

Active language is picked from: `--lang` flag → saved config →
`NETMEDIC_LANG` env → OS locale → `en` fallback. PRs adding more
languages are welcome — see [CONTRIBUTING](CONTRIBUTING.md#adding-a-new-language).

## Acknowledgements

NetMedic is built end-to-end with the help of three excellent
developer tools, gratefully credited below:

- **[JetBrains PyCharm](https://www.jetbrains.com/pycharm/)** — primary
  IDE. Many thanks to **JetBrains** for offering free licenses to
  open-source maintainers through the
  [Open Source Development License](https://www.jetbrains.com/community/opensource/)
  program.
- **[Anthropic Claude Code](https://www.anthropic.com/claude-code)** —
  used as a pair programmer throughout the design, refactor, and
  documentation passes.
- **[OpenAI Codex](https://openai.com/index/openai-codex/)** —
  consulted for second-opinion code reviews and edge-case suggestions.

If you find this project useful, please consider supporting these
vendors by trying their products.

[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" alt="JetBrains Logo"/>](https://www.jetbrains.com/)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm_icon.png" width="64" alt="PyCharm Logo"/>](https://www.jetbrains.com/pycharm/)

## License

MIT © 2026 **Birditch**. See [LICENSE](LICENSE) for the full text.
