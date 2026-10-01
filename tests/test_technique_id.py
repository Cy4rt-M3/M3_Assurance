"""Tests for ATT&CK technique extraction from OCSF events."""

from typing import Any

import pytest

from apps.shared.ocsf import DEFAULT_TECHNIQUE_ID, technique_id_from_event

CASES: list[tuple[dict[str, Any], str]] = [
    ({"finding_info": {"types": ["T1190"]}}, "T1190"),
    ({"finding_info": {"types": ["SQL Injection", "T1190 - Exploit"]}}, "T1190"),
    ({"finding_info": {"types": ["T1059.001"]}}, "T1059.001"),
    (
        {"attack": {"technique_uid": "T1059"}, "finding_info": {"types": ["T1190"]}},
        "T1059",
    ),
    ({"finding_info": {"types": [5, "no technique"]}}, DEFAULT_TECHNIQUE_ID),
    ({"finding_info": {"types": "T1190"}}, DEFAULT_TECHNIQUE_ID),
    ({"finding_info": "T1190"}, DEFAULT_TECHNIQUE_ID),
    ({"attack": "T1190"}, DEFAULT_TECHNIQUE_ID),
    ({}, DEFAULT_TECHNIQUE_ID),
]


@pytest.mark.parametrize(("event", "expected"), CASES)
def test_technique_id_from_event(event: dict[str, Any], expected: str) -> None:
    assert technique_id_from_event(event) == expected
