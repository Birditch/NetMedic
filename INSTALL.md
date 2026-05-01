# Installing NetMedic

NetMedic is shipped as a **pure-Python** package. There is no compiled
binary blob — the same wheel runs on any architecture where Python 3.10+
runs (Windows x64, x86, ARM64, macOS Intel & Apple Silicon, Linux amd64,
arm64, ...). At runtime, NetMedic uses your system's Python interpreter.

> **Why "pure Python" wheels and not per-arch binaries?**  Per-arch binaries
> would require bundling Python itself (PyInstaller, Nuitka). The user
> explicitly asked for "compile, but require Python on the system" — that
> is exactly what a wheel/sdist provides. One wheel, every arch.

## Compatibility matrix (1.0.1 preview beta1)

| OS | Architecture | Install path | Runtime status |
|----|--------------|--------------|----------------|
| Windows 10 / 11 | x64 / x86 / ARM64 | pip / wheel | **Fully supported** |
| macOS 12+ | Intel / Apple Silicon | pip / wheel / Homebrew tap | Pure-Python package/runtime preview; DNS-mutating backend in progress — see ROADMAP |
| Ubuntu / Debian / Arch / Fedora | amd64 / arm64 | pip / wheel | Pure-Python package/runtime preview; resolver backend in progress — see ROADMAP |

## Method 1 — pip (recommended)

Once a release is on PyPI:

```bash
pip install netmedic                  # latest stable
pip install --pre netmedic            # latest preview/beta
```

After install, two equivalent entry points are on `PATH`:

```bash
netmedic                              # interactive launcher
nm                                    # short alias
netmedic check                        # direct subcommand
nm --lang ja status                   # subcommand with global flag
```

## Method 2 — pip from a GitHub release

```bash
pip install https://github.com/Birditch/NetMedic/releases/download/v1.0.1-beta.1/netmedic-1.0.1b1-py3-none-any.whl
```

The wheel and sdist are attached to every Release page. The sdist
(``.tar.gz``) is what Homebrew formulas ultimately consume.

## Method 3 — Homebrew (macOS / Linuxbrew)

A tap-ready formula lives at [`Formula/netmedic.rb`](Formula/netmedic.rb).
Until the homebrew-core PR is open, install via the user tap:

```bash
brew tap birditch/netmedic https://github.com/Birditch/NetMedic
brew install netmedic
```

This brings in `python@3.12` as a runtime dependency and creates
`netmedic` and `nm` shims under `$(brew --prefix)/bin`.

## Method 4 — pipx (isolated)

```bash
pipx install netmedic
```

Best when you don't want NetMedic and its deps in your global
site-packages.

## Method 5 — clone & run from source

```bash
git clone https://github.com/Birditch/NetMedic.git
cd NetMedic
pip install -r requirements.txt
python run.py                          # launcher
python run.py status                   # direct subcommand
```

## Method 6 — apt / Snap / winget / Chocolatey / Scoop

These channels are tracked in [ROADMAP](ROADMAP.md). The blocker for
each is publishing 1.0.1 stable; once that lands the packaging glue
follows.

## Where NetMedic stores state

| Path | What |
|------|------|
| `~/.netmedic/config.json` | Selected language, country, scope, IPv6 preference |
| `~/.netmedic/backups/`    | Pre-`apply` snapshots (per-call + `latest.json`) |
| `~/.netmedic/logs/`       | Reserved for future structured logs |

Set the `NETMEDIC_HOME` environment variable to relocate the entire
state directory (e.g. to a roaming-profile-friendly path on Windows
or a non-default home on Linux).
