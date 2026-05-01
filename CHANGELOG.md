# Changelog

All notable changes to NetMedic will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-30

### Added

- Initial public release.
- Active-adapter discovery (`get-active-adapter`) via PowerShell on
  Windows 10 / 11.
- Connectivity / packet-loss tests against domestic + foreign hosts.
- Public DNS speed benchmark across 11 well-known providers.
- DNS pollution detection: known GFW poison-IP table + sub-floor RTT
  heuristic.
- **DoH speed + pollution benchmark** over real HTTPS:443
  (router-hijack-proof).
- **Smart split DNS** via Windows NRPT — Chinese namespaces routed to a
  domestic DoH, everything else to the user-chosen primary DoH.
- **`force-doh` interactive top-5 picker** with provider, operator,
  region, IPs, latency, and pollution columns.
- IPv6 connectivity probe; v6 DoH IPs registered only when available.
- Atomic backup + one-click `restore`.
- hosts-file helper that respects user-managed lines.
- Multilingual UI: 简体中文, 繁體中文, English, 日本語, 한국어, Русский
  (one JSON per locale under `locales/`).
- MIT license, JetBrains PyCharm acknowledgement.
- GitHub Actions CI: lint + compile-check on Python 3.10/3.11/3.12.
- Issue / PR templates.

### Notes

NetMedic is built and maintained with **JetBrains PyCharm** under their
Open Source Development License program.
