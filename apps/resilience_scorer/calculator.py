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
    """Return the band label for a composite score."""
    for threshold, label in _BANDS:
        if composite <= threshold:
            return label
    return "Resilient"


def composite_score(
    coverage: float,
    detection: float,
    evidence: float,
) -> float:
    """Original Module 3 resilience score."""
    return round(
        coverage * 0.40 + detection * 0.35 + evidence * 0.25,
        1,
    )


def safe_pct(numerator: int, denominator: int) -> float:
    """Return percentage or 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def weighted_risk_score(
    cvss: float,
    epss: float,
    blast_radius: float,
) -> float:
    """
    Calculate overall risk score.

    cvss: 0-10
    epss: 0-1
    blast_radius: 0-100

    Returns:
        Risk score between 0 and 100.
    """

    cvss_score = cvss * 10
    epss_score = epss * 100

    final_score = (cvss_score * 0.50) + (epss_score * 0.30) + (blast_radius * 0.20)

    return round(min(final_score, 100.0), 1)


# if __name__ == "__main__":
# score = weighted_risk_score(
#   cvss=9.2,
#  epss=0.75,
# blast_radius=80,)
# print(score)
