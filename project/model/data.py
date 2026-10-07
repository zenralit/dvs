"""JSON presets and helper functions for fuel and material selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_json(name: str) -> dict[str, Any]:
    with (DATA_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_fuels() -> dict[str, dict[str, Any]]:
    return load_json("fuels.json")


def load_materials() -> dict[str, dict[str, Any]]:
    return load_json("materials.json")
