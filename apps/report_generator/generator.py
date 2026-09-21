"""Compliance report HTML generation. Cyclomatic complexity ≤4."""

import hashlib
from html import escape
from typing import Any

from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.resilience_scorer.models import ResilienceScore

_BAND_CSS: dict[str, str] = {
    "Critical": "#b91c1c",
    "At Risk": "#c2410c",
    "Moderate": "#ca8a04",
    "Strong": "#4d7c0f",
    "Resilient": "#15803d",
}


def content_hash(content: str) -> str:
    """Return the SHA-256 digest of the report content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def content_hash_bytes(content: bytes) -> str:
    """Return the SHA-256 digest of a binary report payload (e.g. PDF)."""
    return hashlib.sha256(content).hexdigest()


def _render_score(score: ResilienceScore) -> str:
    color = _BAND_CSS.get(score.band, "#111827")
    return (
        "<section><h2>Resilience Score</h2>"
        f"<p>Composite score <b>{score.composite_score:.1f}</b> "
        f'<span style="background:{color};color:#fff;padding:2px 8px">'
        f"{escape(score.band)}</span></p>"
        '<table border="1" cellspacing="0" cellpadding="6">'
        f"<tr><th>Control Coverage (40%)</th>"
        f"<td>{score.coverage_score:.1f}</td></tr>"
        f"<tr><th>Detection Effectiveness (35%)</th>"
        f"<td>{score.detection_score:.1f}</td></tr>"
        f"<tr><th>Evidence Completeness (25%)</th>"
        f"<td>{score.evidence_score:.1f}</td></tr>"
        "</table></section>"
    )


def _render_controls(
    statuses: dict[str, str],
    controls: list[Control],
) -> str:
    rows: list[str] = []
    for control in controls:
        status = statuses.get(control.control_id, "Not evaluated")
        rows.append(
            f"<tr><td>{escape(control.framework_id)}</td>"
            f"<td>{escape(control.control_id)}</td>"
            f"<td>{escape(control.name)}</td>"
            f"<td>{escape(status)}</td></tr>"
        )
    return (
        "<section><h2>Control-by-Control Status</h2>"
        '<table border="1" cellspacing="0" cellpadding="6">'
        "<tr><th>Framework</th><th>Control</th><th>Name</th><th>Status</th></tr>"
        + "".join(rows)
        + "</table></section>"
    )


def _render_gaps(gaps: list[GapAnalysis]) -> str:
    rows = [
        f"<tr><td>{escape(gap.control_id)}</td>"
        f"<td>{escape(gap.gap_type)}</td>"
        f"<td>{gap.priority}</td>"
        f"<td>{escape(gap.remediation)}</td></tr>"
        for gap in gaps
    ]
    return (
        "<section><h2>Gap Analysis &amp; Remediation</h2>"
        '<table border="1" cellspacing="0" cellpadding="6">'
        "<tr><th>Control</th><th>Gap Type</th><th>Priority</th>"
        "<th>Remediation</th></tr>" + "".join(rows) + "</table>"
        f"<p>Total gaps: {len(gaps)}</p></section>"
    )


def _render_verdicts(verdicts: list[dict[str, Any]]) -> str:
    rows = [
        f"<tr><td>{escape(str(v.get('verdict_id', '')))}</td>"
        f"<td>{escape(str(v.get('technique_id', '')))}</td>"
        f"<td>{escape(str(v.get('outcome', '')))}</td></tr>"
        for v in verdicts
    ]
    return (
        "<section><h2>Validated Verdicts (Evidence)</h2>"
        '<table border="1" cellspacing="0" cellpadding="6">'
        "<tr><th>Verdict</th><th>Technique</th><th>Outcome</th></tr>"
        + "".join(rows)
        + "</table></section>"
    )


def render_report(
    engagement: dict[str, Any],
    statuses: dict[str, str],
    controls: list[Control],
    verdicts: list[dict[str, Any]],
    score: ResilienceScore,
    gaps: list[GapAnalysis],
) -> str:
    """Render the full compliance report as an HTML document."""
    frameworks = ", ".join(str(f) for f in engagement.get("frameworks", []))

    body = "".join(
        (
            "<h1>Compliance Assessment Report</h1>",
            f"<p>Engagement: {escape(str(engagement.get('engagement_id', '')))}</p>",
            f"<p>Organization: {escape(str(engagement.get('organization', '')))}</p>",
            f"<p>Frameworks: {escape(frameworks)}</p>",
            "<p>Prepared by: CyArt Tech LLP — M3 Assurance</p>",
            _render_score(score),
            _render_verdicts(verdicts),
            _render_controls(statuses, controls),
            _render_gaps(gaps),
        )
    )

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        "<title>Compliance Assessment Report</title></head>"
        f'<body style="font-family:sans-serif">{body}</body></html>'
    )
