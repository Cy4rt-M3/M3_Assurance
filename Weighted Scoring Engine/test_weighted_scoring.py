"""
Tests for the Weighted Scoring Engine.

No mocking needed - this is pure calculation, no external APIs involved.

Run with:
    python -m pytest test_weighted_scoring.py -v
"""

import pytest

from weighted_scoring_engine import (
    calculate_risk_score,
    classify_risk_band,
    save_result,
    score_and_save,
)
from database import RiskScore, get_session, init_db


# --- calculate_risk_score: correctness ---

def test_max_inputs_produce_max_score():
    result = calculate_risk_score(cvss_score=10, epss_score=1.0, blast_radius_score=100)
    assert result["composite_score"] == 100.0
    assert result["risk_band"] == "Critical"


def test_min_inputs_produce_min_score():
    result = calculate_risk_score(cvss_score=0, epss_score=0.0, blast_radius_score=0)
    assert result["composite_score"] == 0.0
    assert result["risk_band"] == "Low"


def test_normalization_scales_correctly():
    # CVSS of 5 -> 50 normalized; EPSS of 0.5 -> 50 normalized
    result = calculate_risk_score(cvss_score=5, epss_score=0.5, blast_radius_score=50)
    assert result["cvss_normalized"] == 50.0
    assert result["epss_normalized"] == 50.0
    assert result["composite_score"] == 50.0


def test_known_worked_example():
    # CVSS=10 (normalized 100) * 0.40 = 40
    # EPSS=0.99999 (normalized ~100) * 0.35 = ~35
    # Blast Radius=86 * 0.25 = 21.5
    # Total ~= 96.5
    result = calculate_risk_score(cvss_score=10, epss_score=0.99999, blast_radius_score=86)
    assert result["composite_score"] == pytest.approx(96.5, abs=0.1)
    assert result["risk_band"] == "Critical"


# --- calculate_risk_score: input validation ---

def test_cvss_out_of_range_raises():
    with pytest.raises(ValueError, match="cvss_score must be between"):
        calculate_risk_score(cvss_score=11, epss_score=0.5, blast_radius_score=50)


def test_epss_out_of_range_raises():
    with pytest.raises(ValueError, match="epss_score must be between"):
        calculate_risk_score(cvss_score=5, epss_score=1.5, blast_radius_score=50)


def test_blast_radius_out_of_range_raises():
    with pytest.raises(ValueError, match="blast_radius_score must be between"):
        calculate_risk_score(cvss_score=5, epss_score=0.5, blast_radius_score=150)


# --- classify_risk_band ---

@pytest.mark.parametrize("score,expected_band", [
    (0, "Low"),
    (39.9, "Low"),
    (40, "Medium"),
    (64.9, "Medium"),
    (65, "High"),
    (84.9, "High"),
    (85, "Critical"),
    (100, "Critical"),
])
def test_risk_band_thresholds(score, expected_band):
    assert classify_risk_band(score) == expected_band


# --- database: upsert behavior ---

@pytest.fixture
def temp_db(tmp_path):
    db_path = str(tmp_path / "test_risk_scores.db")
    init_db(db_path)
    return db_path


def test_save_result_creates_one_row_for_new_pair(temp_db):
    result = calculate_risk_score(cvss_score=8, epss_score=0.7, blast_radius_score=60)
    save_result("CVE-2024-3400", "payment-api-prod", result, temp_db)

    session = get_session(temp_db)
    rows = (
        session.query(RiskScore)
        .filter_by(cve_id="CVE-2024-3400", asset_id="payment-api-prod")
        .all()
    )
    session.close()

    assert len(rows) == 1


def test_save_result_updates_existing_row_instead_of_duplicating(temp_db):
    first = calculate_risk_score(cvss_score=5, epss_score=0.2, blast_radius_score=30)
    second = calculate_risk_score(cvss_score=9, epss_score=0.9, blast_radius_score=80)

    save_result("CVE-2024-3400", "payment-api-prod", first, temp_db)
    save_result("CVE-2024-3400", "payment-api-prod", second, temp_db)  # re-scored

    session = get_session(temp_db)
    rows = (
        session.query(RiskScore)
        .filter_by(cve_id="CVE-2024-3400", asset_id="payment-api-prod")
        .all()
    )
    session.close()

    assert len(rows) == 1  # still just one row, not two
    assert rows[0].cvss_score == 9  # reflects the latest data


def test_different_asset_same_cve_creates_separate_row(temp_db):
    # Same CVE affecting two different assets should be tracked separately
    result = calculate_risk_score(cvss_score=8, epss_score=0.7, blast_radius_score=60)
    save_result("CVE-2024-3400", "asset-a", result, temp_db)
    save_result("CVE-2024-3400", "asset-b", result, temp_db)

    session = get_session(temp_db)
    rows = session.query(RiskScore).filter_by(cve_id="CVE-2024-3400").all()
    session.close()

    assert len(rows) == 2


def test_score_and_save_returns_result_and_persists(temp_db):
    result = score_and_save("CVE-2024-3400", "payment-api-prod", 8, 0.7, 60, temp_db)

    session = get_session(temp_db)
    row = (
        session.query(RiskScore)
        .filter_by(cve_id="CVE-2024-3400", asset_id="payment-api-prod")
        .first()
    )
    session.close()

    assert row is not None
    assert row.composite_score == result["composite_score"]
