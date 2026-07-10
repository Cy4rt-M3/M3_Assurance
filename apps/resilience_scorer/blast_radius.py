"""Blast Radius scoring logic."""

from typing import Literal

Exposure = Literal["internal", "external"]
Criticality = Literal["low", "medium", "high"]


def _exposure_score(exposure: Exposure) -> float:
    return 40.0 if exposure == "external" else 20.0


def _criticality_score(criticality: Criticality) -> float:
    scores = {
        "low": 10.0,
        "medium": 25.0,
        "high": 40.0,
    }
    return scores[criticality]


def _internet_score(internet_facing: bool) -> float:
    return 20.0 if internet_facing else 0.0


def calculate_blast_radius(
    exposure: Exposure,
    criticality: Criticality,
    internet_facing: bool,
) -> float:
    """Calculate Blast Radius score (0–100)."""

    score = (
        _exposure_score(exposure)
        + _criticality_score(criticality)
        + _internet_score(internet_facing)
    )

    return min(score, 100.0)