"""Loads framework + control definitions from apps/framework_registry/definitions/*.json
into validated Framework / Control pydantic models.
"""

import json
from pathlib import Path

from apps.framework_registry.models import Control, Framework

DEFINITIONS_DIR = Path(__file__).parent / "definitions"


def _to_control(raw: dict, framework_id: str) -> Control:
    """Map a raw JSON control entry (function/category/category_id/description)
    onto the Control model
    (control_id/framework_id/category/name/description/attack_mapping)."""
    category = raw.get("category") or raw.get("category_id") or ""
    return Control(
        control_id=raw["control_id"],
        framework_id=framework_id,
        category=category,
        name=raw.get("name") or raw["control_id"],
        description=raw.get("description", ""),
        attack_mapping=raw.get("attack_mapping", []),
    )


def load_framework_file(path: Path) -> tuple[Framework, list[Control]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    framework = Framework(
        framework_id=raw["framework_id"],
        name=raw["name"],
        version=raw["version"],
        description=raw.get("description", ""),
        regions=raw.get("regions", []),
    )

    controls = [_to_control(c, framework.framework_id) for c in raw.get("controls", [])]
    return framework, controls


def load_all_frameworks(
    definitions_dir: Path = DEFINITIONS_DIR,
) -> dict[str, tuple[Framework, list[Control]]]:
    """Scans the definitions directory for *.json files and returns a dict
    keyed by framework_id -> (Framework, [Control, ...])."""
    results: dict[str, tuple[Framework, list[Control]]] = {}
    for path in sorted(definitions_dir.glob("*.json")):
        framework, controls = load_framework_file(path)
        results[framework.framework_id] = (framework, controls)
    return results
