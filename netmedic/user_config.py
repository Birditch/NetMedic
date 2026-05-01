"""Persistent user preferences (selected language, country, scope, IPv6 pref).

Stored at ``~/.netmedic/config.json`` so the file:
- survives ``pip install -U netmedic`` upgrades,
- doesn't leak between user accounts on the same machine,
- doesn't pollute the package install directory (which would be
  read-only for non-root pip installs).

Set ``NETMEDIC_HOME`` to override the storage directory entirely.
"""
from __future__ import annotations
import json
import os
from pathlib import Path


def _data_dir() -> Path:
    override = os.environ.get("NETMEDIC_HOME")
    if override:
        return Path(override)
    return Path.home() / ".netmedic"


CONFIG_PATH = _data_dir() / "config.json"


def load() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def update(**kwargs) -> dict:
    cfg = load()
    cfg.update(kwargs)
    save(cfg)
    return cfg
