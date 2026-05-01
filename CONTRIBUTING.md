# Contributing to NetMedic

Thanks for your interest in NetMedic! This document describes how to
report issues, propose features, contribute code, and add translations.

## Code of conduct

Be respectful and constructive. Off-topic, abusive, or politically
charged comments on PRs / issues will be closed without discussion.

## How to file a good bug report

Open an issue using the **Bug report** template and include:

- Output of `python run.py status`
- Output of `python run.py check` (redact your IPv4 if you'd like)
- Windows version (`winver`)
- Whether you're behind a soft router / VPN, and which one
- Exact command that triggered the bug

## Adding a new DNS provider

NetMedic only ships **uncensored, unfiltered** resolvers. Please do not
PR providers that block adult content, malware, ads, or political
domains — those go in user-side allowlists, not the default catalog.

To add a provider, edit:

- `netmedic/data/public_dns.py` — for the UDP/53 benchmark catalog
- `netmedic/fix/doh.py::DOH_PROVIDERS` — for the DoH catalog

Each entry needs `url`, `region`, `operator`, `notes`, `v4_ips`,
and (optionally) `v6_ips`.

## Adding a new language

1. Copy `locales/en.json` to `locales/<lang-code>.json` (use the
   IETF code, e.g. `de`, `fr`, `pt-BR`).
2. Translate every value. Do **not** translate keys.
3. Add the new code to the `SUPPORTED` list in `netmedic/i18n.py`.
4. Add the locale to `locales/` mention in `README.md`.
5. Open a PR — translations are reviewed for accuracy by native
   speakers when possible.

## Code style

- Python ≥ 3.10, type hints encouraged.
- 4-space indents.
- Run `python -m compileall netmedic` before pushing.
- Keep diffs minimal and focused; one feature/fix per PR.

## Running locally

```powershell
git clone https://github.com/Birditch/netmedic.git
cd netmedic
pip install -r requirements.txt
python run.py status
```

For commands that change system state (`apply`, `restore`, `force-doh`),
launch PowerShell as Administrator first.

## Releases

Maintainers cut a release by bumping `__version__` in
`netmedic/__init__.py`, updating `CHANGELOG.md`, tagging
`vMAJOR.MINOR.PATCH`, and pushing the tag.

## Acknowledgement

This project is developed with **JetBrains PyCharm** under the
[JetBrains Open Source Development License](https://www.jetbrains.com/community/opensource/)
program.
