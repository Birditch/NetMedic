# Security Policy

## Supported versions

NetMedic follows semantic versioning. Security fixes go into the latest
**1.x** release line. Older majors are not patched.

| Version | Supported          |
|---------|--------------------|
| 1.x     | ✅                  |
| < 1.0   | ❌ (pre-release)    |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Use **GitHub's private vulnerability reporting** at
<https://github.com/Birditch/netmedic/security/advisories/new>, or
email the maintainer if listed in the repository profile.

You can expect:

- Acknowledgement within 72 hours.
- A coordinated fix timeline based on severity.
- Credit in the changelog and the published advisory if you wish.

## Threat model

NetMedic runs locally with elevated privileges to modify DNS / NRPT.
Items in scope:

- Privilege escalation via crafted backup / locale files.
- Code injection through user-supplied DNS arguments.
- Path-traversal via the hosts-file marker block.

Out of scope:

- Bypassing the GFW or any state-level DNS censorship — NetMedic is a
  diagnostic and configuration tool, not a circumvention service.
- Bugs in dnspython / httpx / typer / rich (please report upstream).
