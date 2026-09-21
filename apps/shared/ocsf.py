"""OCSF event conversion helpers. Cyclomatic complexity ≤4."""

import hashlib
import json
from typing import Any, cast

DEFAULT_TECHNIQUE_ID = "T1078"

_SEVERITY_NAMES: dict[int, str] = {
    0: "Unknown",
    1: "Informational",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Critical",
}

_DISPOSITION_OUTCOMES: dict[str, str] = {
    "Blocked": "Detected",
    "Detected": "Detected",
    "Allowed": "Detected",
    "Missed": "Missed",
    "No Data": "No Data",
    "None": "No Data",
}


def outcome_from_disposition(disposition: str) -> str:
    """Map an OCSF disposition to a Module 2 verdict outcome."""
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
    return {
        "verdict_id": verdict_id,
        "engagement_id": engagement_id,
        "technique_id": technique_id_from_event(event),
        "outcome": outcome_from_disposition(str(event.get("disposition") or "")),
        "severity_id": severity_id_from_event(event),
        "evidence_hash": evidence_hash(event),
    }
