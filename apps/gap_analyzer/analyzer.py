"""Gap analysis logic. Cyclomatic complexity ≤4 guaranteed."""

from typing import Any

from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.shared.attack_tactics import effective_mapping

_UNCOVERED_NOT_MET_PRIORITY = 1
_UNCOVERED_PARTIAL_PRIORITY = 3
_EVIDENCE_GAP_PRIORITY = 3


def priority_for_verdict(verdict: dict[str, Any]) -> int:
    """Map a verdict severity id to a 1-5 gap priority."""
    severity_id = int(verdict.get("severity_id", 0))
    if severity_id >= 4:
        return 1
    if severity_id == 3:
        return 2
    return 3


def remediation_techniques(
    control: Control,
    tested: set[str],
) -> str:
    """Join the effective techniques into a remediation hint."""
    return ", ".join(effective_mapping(control.attack_mapping, tested))


def _uncovered_gap(
    engagement_id: str,
    control_id: str,
    status: str,
    remediation: str,
    index: int,
) -> GapAnalysis:
    priority = (
        _UNCOVERED_NOT_MET_PRIORITY
        if status == "Not Met"
        else _UNCOVERED_PARTIAL_PRIORITY
    )
    return GapAnalysis(
        analysis_id=f"{engagement_id}-gap-{index:04d}",
        engagement_id=engagement_id,
        control_id=control_id,
        gap_type="uncovered_control",
        priority=priority,
        remediation=remediation,
    )


def _verdict_gap(
    engagement_id: str,
    control_id: str,
    verdict: dict[str, Any],
    index: int,
) -> GapAnalysis:
    missed = verdict["outcome"] == "Missed"
    return GapAnalysis(
        analysis_id=f"{engagement_id}-gap-{index:04d}",
        engagement_id=engagement_id,
        control_id=control_id,
        gap_type="missed_detection" if missed else "evidence_gap",
        priority=priority_for_verdict(verdict) if missed else _EVIDENCE_GAP_PRIORITY,
        remediation=(
            f"Deploy detection rule for {verdict['technique_id']}"
            if missed
            else f"Capture evidence for {verdict['technique_id']}"
        ),
    )


def _control_gap(
    engagement_id: str,
    status: str,
    control: Control,
    tested: set[str],
    index: int,
) -> GapAnalysis:
    """Build an uncovered-control gap for a control requiring action."""
    technique_hint = remediation_techniques(control, tested)
    if status == "Not Met":
        remediation = f"Deploy detection or compensating control for {technique_hint}"
    else:
        remediation = (
            f"Complete validation and strengthen detection for {technique_hint}"
        )
    return _uncovered_gap(engagement_id, control.control_id, status, remediation, index)


_GAP_TYPE_BY_OUTCOME: dict[str, str] = {
    "Missed": "missed_detection",
    "No Data": "evidence_gap",
}


def _first_candidate_control(
    technique_id: str,
    controls: list[Control],
    tested: set[str],
) -> Control | None:
    """Return the first control the technique maps to, or None."""
    for control in controls:
        if technique_id not in effective_mapping(control.attack_mapping, tested):
            continue
        return control
    return None


def _verdict_gaps_for(
    engagement_id: str,
    verdict: dict[str, Any],
    controls: list[Control],
    tested: set[str],
    seen: set[tuple[str, str]],
    index: int,
) -> list[GapAnalysis]:
    """Build the deduplicated gaps triggered by a single verdict."""
    if verdict["outcome"] not in ("Missed", "No Data"):
        return []
    control = _first_candidate_control(verdict["technique_id"], controls, tested)
    if control is None:
        return []
    gap_type = _GAP_TYPE_BY_OUTCOME[verdict["outcome"]]
    key = (gap_type, control.control_id)
    if key in seen:
        return []
    seen.add(key)
    return [_verdict_gap(engagement_id, control.control_id, verdict, index)]


def _control_by_id(
    controls: list[Control],
    control_id: str,
) -> Control | None:
    """Return the control with the given id, or None when missing."""
    for control in controls:
        if control.control_id == control_id:
            return control
    return None


def _gaps_from_statuses(
    engagement_id: str,
    statuses: dict[str, str],
    controls: list[Control],
    tested: set[str],
) -> tuple[list[GapAnalysis], set[tuple[str, str]]]:
    """Build uncovered-control gaps and the deduplication keys they added."""
    gaps: list[GapAnalysis] = []
    seen: set[tuple[str, str]] = set()
    for control_id, status in statuses.items():
        control = _control_by_id(controls, control_id)
        if status not in ("Not Met", "Partial") or control is None:
            continue
        gaps.append(_control_gap(engagement_id, status, control, tested, len(gaps)))
        seen.add(("uncovered_control", control_id))
    return gaps, seen


def analyze(
    engagement_id: str,
    statuses: dict[str, str],
    verdicts: list[dict[str, Any]],
    controls: list[Control],
) -> list[GapAnalysis]:
    """Produce the prioritized gap list for an engagement."""
    tested = {v["technique_id"] for v in verdicts}
    gaps, seen = _gaps_from_statuses(engagement_id, statuses, controls, tested)

    for verdict in verdicts:
        gaps.extend(
            _verdict_gaps_for(engagement_id, verdict, controls, tested, seen, len(gaps))
        )

    return gaps
