"""Certainty vs Chance: how economic shocks change what persuades shoppers (UK vs UAE, 2019-2026)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"


def load_yaml(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as f:
        return yaml.safe_load(f)
