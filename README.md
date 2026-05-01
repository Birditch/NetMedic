# NetMedic — Network Doctor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](netmedic/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](#requirements)
[![CI](https://github.com/Birditch/netmedic/actions/workflows/ci.yml/badge.svg)](https://github.com/Birditch/netmedic/actions/workflows/ci.yml)

> **A diagnostic and repair tool for DNS / connectivity issues on Windows, with first-class support for the "China + soft-router-via-Japan" topology that breaks naive DNS configurations.**

NetMedic measures, diagnoses, and (with consent) repairs the most common
classes of DNS/network issues — including the kind silently caused by a
soft router that hijacks UDP/53 on the LAN.

---

## Why this exists

A typical pain pattern: traffic exits via a Japan node through a soft router
(OpenWrt/iKuai/Padavan/...). Most things work, but:

- Google search loads slowly, then "magically" works after a refresh
- "Sign in with QQ" / WeChat quick-login can't see your active QQ session
- 12306 / Taobao / Bilibili sometimes fall back to the slow Japan path
- DNS leaks bypass your privacy settings

The root cause is almost always one of:

- **DNS poisoning** at UDP/53 (GFW packet injection)
- **Soft-router DNS hijacking** that forces every port-53 query through
  a local resolver, even when you've changed Windows DNS settings
- **Wrong-region DNS answers** sending Chinese services through the Japan
  exit (slow + triggers risk control)

NetMedic finds which of these you're actually hit by, and offers honest
fixes — including using **Windows 11 native DoH (HTTPS:443)** to bypass
soft-router port-53 interception entirely.

## Features

- **Full network checkup** — adapter info, ping/loss against domestic + foreign
  hosts, MTU sanity, all in one command
- **Public DNS speed ranking** — UDP latency benchmark across 11 well-known
  resolvers
- **Pollution detection** — checks each DNS against known GFW poison-IP
  table + sub-floor latency heuristic
- **DoH speed + pollution benchmark** — real HTTPS:443 measurements that
  cannot be faked by a port-53 hijack
- **Interactive top-5 picker** — select among the fastest *clean* DoH
  providers, with provider/operator/region/IPs/notes
- **Smart split DNS** — `*.qq.com / *.taobao.com / *.bilibili.com / 94 more`
  always go to a Chinese DoH for region-correct answers, written via Windows
  native NRPT (Name Resolution Policy Table)
- **IPv6-aware** — auto-detects v6 connectivity, registers v6 DoH IPs only
  when you actually have a working v6 path
- **Atomic backup + one-click restore** — every `apply` snapshots prior DNS
  state to `backups/latest.json`; `restore` puts it back
- **Hosts file helper** — manages a `# >>> NetMedic >>>` block, never touches
  user-added entries
- **Multilingual UI** — 6 languages: 简体中文 / 繁體中文 / English / 日本語 /
  한국어 / Русский (see [Internationalization](#internationalization))

## Requirements

| Component | Version |
|---|---|
| Operating system | Windows 10 or **Windows 11** (DoH features require 11) |
| Python | 3.10+ |
| Privileges | Administrator for `apply`, `restore`, `force-doh` |

Dependencies are pinned in [`requirements.txt`](requirements.txt):
[`dnspython`](https://www.dnspython.org/) (with `httpx` + `h2` for DoH),
[`rich`](https://github.com/Textualize/rich), and
[`typer`](https://typer.tiangolo.com/).

## Installation

```powershell
git clone https://github.com/Birditch/netmedic.git
cd netmedic
pip install -r requirements.txt
```

## Usage

All commands are accessible through `python run.py <command>`.

### Network checkup (no admin)

```powershell
python run.py check
```

Tests connectivity, benchmarks 11 public DNS, runs pollution detection,
and reports MTU. Skips: `--skip-speed`, `--skip-pollution`.

### Recommend best DNS (no admin, no system change)

```powershell
python run.py recommend
```

Speed-tests + pollution-checks all known providers, prints a recommendation,
and explicitly **detects** the case where every overseas DNS responds in
< 5 ms (a fingerprint of soft-router DNS hijacking) and offers prioritized
remediation.

### Apply with smart split (admin)

```powershell
python run.py apply
```

Picks the fastest clean foreign DNS for default, fastest clean Chinese DNS
for `*.qq.com / *.taobao.com / ...`, writes NRPT rules, sets adapter DNS,
flushes cache. Backs up first; `restore` reverses everything.

Manual override: `--cn-dns 223.5.5.5,119.29.29.29 --intl-dns 1.1.1.1,8.8.8.8`.

### Force DoH — bypass port-53 hijack (admin, **Windows 11**)

```powershell
python run.py force-doh
```

The command will:

1. Detect IPv6 availability.
2. Run real-HTTPS DoH benchmarks + pollution checks against every provider.
3. Print the result table (provider / operator / region / latency / pollution).
4. Show a **Top 5 selection menu** of the fastest clean DoH endpoints —
   pick one with `1`–`5`.
5. Register the DoH templates with Windows, set the adapter to those IPs,
   and let Windows auto-upgrade to DoH (port 443) — soft router cannot
   intercept HTTPS-encrypted DNS.
6. Always pin Chinese namespaces to AliDNS/DNSPod DoH via NRPT for correct
   region answers.

Verification:

- Open `https://1.1.1.1/help` — should report `Using DNS over HTTPS (DoH): Yes`.
- Re-test "Sign in with QQ" / Google.

### Other commands

```powershell
python run.py bench-doh          # speed + pollution table only, no changes
python run.py status             # current adapter + NRPT rules
python run.py flush              # ipconfig /flushdns
python run.py restore            # roll back to backups/latest.json
```

## How NetMedic decides what's "best"

```
1. UDP DNS speed bench  → average / median / success%
2. Pollution score      → known poison IPs, sub-floor RTT (< 5 ms)
3. DoH HTTPS bench      → ground truth (router-proof)
4. Filter clean         → drop polluted/suspicious/timeout
5. Sort by avg latency  → present top 5
6. User picks           → register DoH templates, set DNS, write NRPT
```

The top-5 menu always includes operator, region, latency, and v4/v6 IPs so
you can pick by your own preference (e.g. "I prefer Cloudflare over Google
even at +50 ms").

## Internationalization

Locale files live under [`locales/`](locales/) — one JSON per language:

- [`en.json`](locales/en.json) — English
- [`zh-CN.json`](locales/zh-CN.json) — 简体中文
- [`zh-TW.json`](locales/zh-TW.json) — 繁體中文
- [`ja.json`](locales/ja.json) — 日本語
- [`ko.json`](locales/ko.json) — 한국어
- [`ru.json`](locales/ru.json) — Русский

The active language is picked from (priority): `--lang` flag → `NETMEDIC_LANG`
env var → OS locale → `en` fallback.

```powershell
$env:NETMEDIC_LANG = "ja"
python run.py check
```

PRs adding more languages are welcome.

## Project layout

```
NetMedic/
├── LICENSE                 # MIT
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── requirements.txt
├── run.py                  # convenience entry: python run.py <cmd>
├── locales/                # i18n: 6 supported languages
├── netmedic/
│   ├── __init__.py         # version + author
│   ├── cli.py              # typer commands
│   ├── config.py           # tunables, test domains, poison-IP table
│   ├── i18n.py             # JSON-backed translation loader
│   ├── reporter.py         # rich tables + panels
│   ├── utils.py            # PowerShell wrapper, admin check
│   ├── data/
│   │   ├── public_dns.py   # public DNS catalog (UDP)
│   │   └── cn_domains.py   # 94 namespaces for split-DNS
│   ├── detect/
│   │   ├── adapter.py      # active interface discovery
│   │   ├── connectivity.py # ping / packet loss
│   │   ├── dns_speed.py    # UDP DNS benchmark
│   │   ├── dns_pollution.py# poison detection
│   │   ├── doh_speed.py    # DoH HTTPS benchmark + pollution
│   │   ├── ipv6.py         # IPv6 availability probe
│   │   └── mtu.py          # MTU sanity
│   └── fix/
│       ├── backup.py       # state snapshots
│       ├── dns_apply.py    # Set-DnsClientServerAddress wrapper
│       ├── doh.py          # Add-DnsClientDohServerAddress wrapper
│       ├── nrpt.py         # NRPT split DNS rules
│       ├── hosts.py        # hosts file marker block
│       └── flush.py        # ipconfig /flushdns
└── .github/
    ├── workflows/ci.yml
    └── ISSUE_TEMPLATE/
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, translation PRs, and
new DNS providers (uncensored only) are welcome.

## Acknowledgements

Powered by **[JetBrains PyCharm](https://www.jetbrains.com/pycharm/)** —
this project is developed entirely with PyCharm Professional. Many thanks
to **JetBrains** for offering free licenses to open-source maintainers
through the [Open Source Development License](https://www.jetbrains.com/community/opensource/)
program — it has made building polished developer tools like NetMedic
sustainable for independent authors.

If you find this project useful and you ship Python yourself, please
consider supporting JetBrains by trying their products.

[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" alt="JetBrains Logo"/>](https://www.jetbrains.com/)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm_icon.png" width="64" alt="PyCharm Logo"/>](https://www.jetbrains.com/pycharm/)

## License

MIT © 2026 **Birditch**. See [LICENSE](LICENSE) for the full text.
