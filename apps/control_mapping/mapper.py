"""Control mapping logic. Cyclomatic complexity ≤4 guaranteed."""

from typing import Any

from apps.control_mapping.models import ControlMappingRequest
from apps.evidence_aggregator.models import EvidenceLink
from apps.framework_registry.models import Control
from apps.shared.attack_tactics import effective_mapping

_OUTCOME_WEIGHT: dict[str, int] = {
    "Detected": 0,
    "Partial": 1,
    "Missed": 2,
    "No Data": 2,
}

_OUTCOME_STATUS: dict[str, str] = {
    "Detected": "Met",
    "Partial": "Partial",
}


def control_id_from_verdict(control_id: str, verdict_id: str) -> str:
    """Build a deterministic evidence link id from control and verdict ids."""
    return f"{control_id}:{verdict_id}"


def evidence_for_control(
    control: Control,
    verdicts: list[dict[str, Any]],
) -> str | None:
    """Return the first evidence hash from a verdict mapped to the control."""
    tested = {v["technique_id"] for v in verdicts}
    effective = effective_mapping(control.attack_mapping, tested)
    for verdict in verdicts:
        if verdict["technique_id"] in effective:
            return verdict["evidence_hash"]
    return None


def technique_statuses(
    verdicts: list[dict[str, Any]],
) -> dict[str, set[str]]:
    """Group verdict outcomes by technique id."""
    grouped: dict[str, set[str]] = {}
    for verdict in verdicts:
        grouped.setdefault(verdict["technique_id"], set()).add(verdict["outcome"])
    return grouped


def relevant_techniques(
    attack_mapping: list[str],
    tested_techniques: set[str],
) -> list[str]:
    """Return the mapping techniques that the engagement actually evaluated."""
    return [t for t in attack_mapping if t in tested_techniques]


def _verdict_outcome(outcomes: set[str]) -> str:
    """Return the deciding outcome for a technique from its outcome set."""
    for label in ("Detected", "Partial", "Missed", "No Data"):
        if label in outcomes:
            return label
    return "No Data"


def mapped_control_status(
    attack_mapping: list[str],
    tested_techniques: set[str],
    grouped: dict[str, set[str]],
) -> str | None:
    """Return the worst-case control status, or None when not applicable."""
    relevant = relevant_techniques(attack_mapping, tested_techniques)
    if not relevant:
        return None

    worst = 0
    status: str | None = None
    for technique in relevant:
        outcome = _verdict_outcome(grouped.get(technique, set()))
        weight = _OUTCOME_WEIGHT[outcome]
        if weight >= worst:
            worst = weight
            status = _OUTCOME_STATUS.get(outcome, "Not Met")
    return status


def _append_evidence_links(
    control_id: str,
    effective: list[str],
    verdicts: list[dict[str, Any]],
    links: list[EvidenceLink],
) -> None:
    """Append evidence links for Detected verdicts mapped to the control."""
    for verdict in verdicts:
        if verdict["technique_id"] not in effective:
            continue
        if verdict["outcome"] != "Detected":
            continue
        links.append(
            EvidenceLink(
                link_id=control_id_from_verdict(control_id, verdict["verdict_id"]),
                control_id=control_id,
                verdict_id=verdict["verdict_id"],
                evidence_hash=verdict["evidence_hash"],
                chain_position=len(links),
            )
        )


def build_mapping(
    controls: list[Control],
    verdicts: list[dict[str, Any]],
) -> tuple[dict[str, str], list[EvidenceLink]]:
    """Map verdicts to control statuses and their evidence links."""
    tested = {v["technique_id"] for v in verdicts}
    grouped = technique_statuses(verdicts)

    statuses: dict[str, str] = {}
    links: list[EvidenceLink] = []

    for control in controls:
        control_id = control.control_id
        effective = effective_mapping(control.attack_mapping, tested)
        if not effective:
            continue

        status = mapped_control_status(effective, tested, grouped)
        if status is None:
            continue

        statuses[control_id] = status
        _append_evidence_links(control_id, effective, verdicts, links)

    return statuses, links


def request_frameworks(
    request: ControlMappingRequest,
    engagement_frameworks: list[str],
) -> list[str]:
    """Resolve the frameworks to map against for a request."""
    return request.framework_ids or engagement_frameworks
