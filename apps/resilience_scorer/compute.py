"""Resilience score assembly. Cyclomatic complexity ≤4."""

from apps.control_mapping.mappers import coverage_pct
from apps.evidence_aggregator.chain_validator import completeness_pct
from apps.resilience_scorer.calculator import (
    composite_score,
    safe_pct,
    score_band,
)
from apps.resilience_scorer.models import ResilienceScore


def assemble_score(
    score_id: str,
    engagement_id: str,
    statuses: dict[str, str],
    total_verdicts: int,
    detected_verdicts: int,
    linked_events: int,
    expected_events: int,
) -> ResilienceScore:
    """Combine the three weighted components into a persisted score."""
    coverage = coverage_pct(statuses)
    detection = safe_pct(detected_verdicts, total_verdicts)
    evidence = completeness_pct(linked_events, expected_events)
    composite = composite_score(coverage, detection, evidence)

    return ResilienceScore(
        score_id=score_id,
        engagement_id=engagement_id,
        composite_score=composite,
        coverage_score=coverage,
        detection_score=detection,
        evidence_score=evidence,
        band=score_band(composite),
    )
