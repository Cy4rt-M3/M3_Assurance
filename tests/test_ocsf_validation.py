"""Tests for OCSF event schema validation."""

import pytest
from pydantic import ValidationError

from apps.evidence_aggregator.models import IngestRequest
from apps.shared.ocsf import event_problems, severity_name, validate_events

VALID: dict[str, object] = {
    "class_uid": 3002,
    "type_uid": 300201,
    "activity_id": 1,
    "severity_id": 1,
}
MINIMAL: dict[str, object] = {"class_uid": 4001, "type_uid": 400101}


def test_valid_event_has_no_problems() -> None:
    assert event_problems(VALID) == []


def test_minimal_event_needs_only_required_fields() -> None:
    assert event_problems(MINIMAL) == []


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        ({"class_uid": "3002", "type_uid": 1}, ["class_uid must be an integer"]),
        ({**MINIMAL, "activity_id": "ONE"}, ["activity_id must be an integer"]),
        ({"activity_id": 1}, ["class_uid is required", "type_uid is required"]),
        ({**MINIMAL, "severity_id": 99}, ["severity_id must be between 0 and 6"]),
        ({**MINIMAL, "severity_id": -1}, ["severity_id must be between 0 and 6"]),
        ({**MINIMAL, "severity_id": "3"}, ["severity_id must be an integer"]),
        ({**MINIMAL, "class_uid": True}, ["class_uid must be an integer"]),
    ],
)
def test_malformed_events_report_every_problem(
    event: dict[str, object], expected: list[str]
) -> None:
    assert event_problems(event) == expected


def test_severity_six_is_valid_and_named() -> None:
    assert event_problems({**MINIMAL, "severity_id": 6}) == []
    assert severity_name(6) == "Fatal"


def test_validate_events_returns_valid_events_unchanged() -> None:
    events = [VALID, MINIMAL]
    assert validate_events(events) == events


def test_validate_events_names_the_bad_event_index() -> None:
    with pytest.raises(ValueError, match=r"events\[1\]: class_uid is required"):
        validate_events([VALID, {"type_uid": 1}])


def test_ingest_request_rejects_malformed_events() -> None:
    with pytest.raises(ValidationError, match=r"events\[0\]"):
        IngestRequest(engagement_id="e1", events=[{"class_uid": "3002"}])


def test_ingest_request_accepts_valid_events() -> None:
    request = IngestRequest(engagement_id="e1", events=[VALID])
    assert request.events == [VALID]
