"""Persistent user preferences (selected language, country, last menu choice).

Stored as JSON next to the project root so the user can wipe state by
deleting one file. Anything missing falls back to safe defaults.
"""
from __future__ import annotations
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / ".netmedic_config.json"


def load() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def update(**kwargs) -> dict:
    cfg = load()
    cfg.update(kwargs)
    save(cfg)
    return cfg
