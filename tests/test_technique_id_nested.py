"""Tests for nested and list-based ATT&CK technique extraction in OCSF events."""

from typing import Any

import pytest

from apps.shared.ocsf import DEFAULT_TECHNIQUE_ID, technique_id_from_event


@pytest.mark.parametrize("key", ["uid", "id"])
def test_attack_nested_technique_dict(key: str) -> None:
    event: dict[str, Any] = {"attack": {"technique": {key: "T1190"}}}
    assert technique_id_from_event(event) == "T1190"


def test_attack_technique_not_a_dict_falls_through() -> None:
    event: dict[str, Any] = {"attack": {"technique": "T1190"}}
    assert technique_id_from_event(event) == DEFAULT_TECHNIQUE_ID


def test_attacks_list_returns_first_technique() -> None:
    event: dict[str, Any] = {
        "attacks": [
            "not-a-dict",
            {"tactic": {"name": "Initial Access"}},
            {"technique": {"uid": "T1190"}},
            {"technique": {"uid": "T1059"}},
        ]
    }
    assert technique_id_from_event(event) == "T1190"


def test_attacks_list_without_technique_falls_through() -> None:
    event: dict[str, Any] = {"attacks": [{"tactic": {"name": "Initial Access"}}, "x"]}
    assert technique_id_from_event(event) == DEFAULT_TECHNIQUE_ID
