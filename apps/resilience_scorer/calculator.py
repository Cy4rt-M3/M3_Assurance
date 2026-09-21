"""Resilience score calculation helpers. Cyclomatic complexity ≤4."""

# Band thresholds: (upper_bound_inclusive, label)
_BANDS: tuple[tuple[float, str], ...] = (
    (40.0, "Critical"),
    (60.0, "At Risk"),
    (75.0, "Moderate"),
    (90.0, "Strong"),
    (100.0, "Resilient"),
)


def score_band(composite: float) -> str:
    """Return the band label for a composite score. Complexity=3."""
    for threshold, label in _BANDS:
        if composite <= threshold:
            return label
    return "Resilient"


def composite_score(coverage: float, detection: float, evidence: float) -> float:
    """Weighted composite: 40% coverage + 35% detection + 25% evidence."""
    return round(coverage * 0.40 + detection * 0.35 + evidence * 0.25, 1)


def safe_pct(numerator: int, denominator: int) -> float:
    """Return (numerator/denominator)*100 or 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 1)


def weighted_risk_score(
    cvss: float,
    epss: float,
    blast_radius: float,
) -> float:
    """Combine CVSS, EPSS and blast radius into a 0-100 risk score."""
    cvss_score = cvss * 10
    epss_score = epss * 100
    score = cvss_score * 0.50 + epss_score * 0.30 + blast_radius * 0.20
    return round(min(score, 100.0), 1)


def severity_to_score(severity_id: int) -> float:
    """Map an OCSF severity id to a 0-100 detection risk score."""
    step = 20
    clamped = max(0, min(severity_id, 5))
    return float(clamped * step)
