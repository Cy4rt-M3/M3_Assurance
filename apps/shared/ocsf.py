"""OCSF event conversion helpers. Cyclomatic complexity <=4."""

import hashlib
import json
from typing import Any, TypeGuard, cast

DEFAULT_TECHNIQUE_ID = "T1078"

_SEVERITY_NAMES: dict[int, str] = {
    0: "Unknown",
    1: "Informational",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Critical",
    6: "Fatal",
}

_DISPOSITION_OUTCOMES: dict[str, str] = {
    "Blocked": "Detected",
    "Detected": "Detected",
    "Allowed": "Detected",
    "Missed": "Missed",
    "No Data": "No Data",
    "None": "No Data",
}

_FIELD_RULES: tuple[tuple[str, bool], ...] = (
    ("class_uid", True),
    ("type_uid", True),
    ("activity_id", False),
    ("severity_id", False),
)
_MAX_SEVERITY_ID = 6


def outcome_from_disposition(disposition: str | None) -> str:
    """Map an OCSF disposition to a Module 2 verdict outcome.

    A missing disposition (Python None) means no data was recorded.
    The literal string "None" is also treated as No Data.
    Any other unrecognized value (including empty string) is Partial.
    """
    if disposition is None:
        return "No Data"
    return _DISPOSITION_OUTCOMES.get(disposition, "Partial")


def _nonempty_str(value: Any) -> str | None:
    """Return value when it is a non-empty string, else None."""
    if isinstance(value, str) and value:
        return value
    return None


def _top_level_technique_id(event: dict[str, Any]) -> str | None:
    """Return the first non-empty top-level technique identifier found."""
    for key in ("technique_uid", "technique_id", "technique"):
        candidate = _nonempty_str(event.get(key))
        if candidate is not None:
            return candidate
    return None


def technique_id_from_event(event: dict[str, Any]) -> str:
    """Extract the ATT&CK technique id from an OCSF event."""
    nested = event.get("attack")
    raw: str | None = None
    if isinstance(nested, dict):
        attack = cast("dict[str, Any]", nested)
        raw = _nonempty_str(attack.get("technique_uid"))
    if raw is not None:
        return raw
    return _top_level_technique_id(event) or DEFAULT_TECHNIQUE_ID


def severity_name(severity_id: int) -> str:
    """Return the OCSF severity label for a numeric severity id."""
    return _SEVERITY_NAMES.get(severity_id, "Unknown")


def severity_id_from_event(event: dict[str, Any]) -> int:
    """Return a safe numeric severity id from an OCSF event."""
    raw = event.get("severity_id", 0)
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    if isinstance(raw, int):
        return raw
    return 0


def _is_int(value: object) -> TypeGuard[int]:
    """Return True for real integers (bool is not accepted)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _int_problem(event: dict[str, Any], name: str, *, required: bool) -> str | None:
    """Describe why field `name` is invalid, or None when it is fine."""
    if name not in event:
        return f"{name} is required" if required else None
    if not _is_int(event[name]):
        return f"{name} must be an integer"
    return None


def _severity_problem(event: dict[str, Any]) -> str | None:
    """Reject severity ids outside the valid OCSF range 0-6."""
    value = event.get("severity_id")
    if _is_int(value) and not (0 <= value <= _MAX_SEVERITY_ID):
        return f"severity_id must be between 0 and {_MAX_SEVERITY_ID}"
    return None


def event_problems(event: dict[str, Any]) -> list[str]:
    """Return every schema problem in one OCSF event (empty when valid)."""
    found = [_int_problem(event, n, required=r) for n, r in _FIELD_RULES]
    found.append(_severity_problem(event))
    return [problem for problem in found if problem is not None]


def validate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return events unchanged, or raise ValueError listing every problem."""
    errors = [
        f"events[{index}]: {problem}"
        for index, event in enumerate(events)
        for problem in event_problems(event)
    ]
    if errors:
        raise ValueError("; ".join(errors))
    return events


def evidence_hash(event: dict[str, Any]) -> str:
    """Return the SHA-256 digest of the canonical event JSON."""
    payload = json.dumps(event, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verdict_data(
    event: dict[str, Any],
    verdict_id: str,
    engagement_id: str,
) -> dict[str, Any]:
    """Build the row payload for the verdicts table from an OCSF event."""
    raw_disposition = event.get("disposition")
    disposition = str(raw_disposition) if raw_disposition is not None else None
    return {
        "verdict_id": verdict_id,
        "engagement_id": engagement_id,
        "technique_id": technique_id_from_event(event),
        "outcome": outcome_from_disposition(disposition),
        "severity_id": severity_id_from_event(event),
        "evidence_hash": evidence_hash(event),
    }
