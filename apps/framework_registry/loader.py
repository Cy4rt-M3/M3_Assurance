"""Load Framework Registry definitions from JSON files. Complexity ≤4 guaranteed."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from apps.framework_registry.models import Control, CrossWalk, Framework

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"


def _load_json(filename: str) -> list[dict[str, Any]]:
    """Read and parse a JSON definitions file."""
    path = _DEFINITIONS_DIR / filename
    with path.open(encoding="utf-8") as f:
        result: list[dict[str, Any]] = json.load(f)
        return result


@lru_cache(maxsize=1)
def load_frameworks() -> tuple[Framework, ...]:
    """Load all frameworks from frameworks.json."""
    raw = _load_json("frameworks.json")
    return tuple(Framework(**item) for item in raw)


@lru_cache(maxsize=1)
def load_controls() -> tuple[Control, ...]:
    """Load all controls from controls.json."""
    raw = _load_json("controls.json")
    return tuple(Control(**item) for item in raw)


@lru_cache(maxsize=1)
def load_crosswalks() -> tuple[CrossWalk, ...]:
    """Load all crosswalks from crosswalks.json."""
    raw = _load_json("crosswalks.json")
    return tuple(CrossWalk(**item) for item in raw)


def get_framework(framework_id: str) -> Framework | None:
    """Return a single framework by id, or None if not found."""
    for fw in load_frameworks():
        if fw.framework_id == framework_id:
            return fw
    return None


def get_controls_for_framework(framework_id: str) -> tuple[Control, ...]:
    """Return all controls belonging to a given framework id."""
    return tuple(c for c in load_controls() if c.framework_id == framework_id)


def get_crosswalks_for_control(control_id: str) -> tuple[CrossWalk, ...]:
    """Return all crosswalks originating from a given control id."""
    return tuple(cw for cw in load_crosswalks() if cw.source_control_id == control_id)
