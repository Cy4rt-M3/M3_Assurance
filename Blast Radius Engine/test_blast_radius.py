"""
Tests for the Blast Radius Engine.

No mocking needed here - unlike Task 1, this logic doesn't call any
external API, so tests run against the real functions directly.

Run with:
    python -m pytest test_blast_radius.py -v
"""

import pytest

from blast_radius_engine import (
    calculate_blast_radius,
    save_result,
    score_and_save,
)
from database import BlastRadiusScore, get_session, init_db


# --- calculate_blast_radius: correctness ---

def test_internet_facing_critical_scores_high():
    result = calculate_blast_radius("srv-1", "internet_facing", "critical", 50)
    assert result["blast_radius_score"] > 85


def test_isolated_low_criticality_scores_low():
    result = calculate_blast_radius("srv-2", "isolated", "low", 0)
    assert result["blast_radius_score"] < 15


def test_connectivity_score_caps_at_100():
    result = calculate_blast_radius("srv-3", "internal_network", "medium", 1000)
    assert result["connectivity_score"] == 100.0


def test_case_insensitive_inputs_accepted():
    result = calculate_blast_radius("srv-4", "INTERNET_FACING", "Critical", 10)
    assert result["exposure_level"] == "internet_facing"
    assert result["criticality"] == "critical"


def test_weights_sum_correctly():
    # exposure=100, criticality=100, connectivity=100 -> composite should be exactly 100
    result = calculate_blast_radius("srv-5", "internet_facing", "critical", 50)
    assert result["blast_radius_score"] == 100.0


# --- calculate_blast_radius: error handling ---

def test_invalid_exposure_level_raises():
    with pytest.raises(ValueError, match="Unknown exposure_level"):
        calculate_blast_radius("srv-6", "not_a_real_level", "critical", 5)


def test_invalid_criticality_raises():
    with pytest.raises(ValueError, match="Unknown criticality"):
        calculate_blast_radius("srv-7", "internal_network", "not_a_real_level", 5)


def test_negative_connections_raises():
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_blast_radius("srv-8", "internal_network", "medium", -1)


# --- database: upsert behavior ---

@pytest.fixture
def temp_db(tmp_path):
    """A fresh, throwaway SQLite file per test - doesn't touch your real data."""
    db_path = str(tmp_path / "test_blast_radius.db")
    init_db(db_path)
    return db_path


def test_save_result_creates_one_row_for_new_asset(temp_db):
    result = calculate_blast_radius("srv-9", "dmz", "high", 10)
    save_result(result, temp_db)

    session = get_session(temp_db)
    rows = session.query(BlastRadiusScore).filter_by(asset_id="srv-9").all()
    session.close()

    assert len(rows) == 1


def test_save_result_updates_existing_row_instead_of_duplicating(temp_db):
    first = calculate_blast_radius("srv-10", "isolated", "low", 1)
    second = calculate_blast_radius("srv-10", "internet_facing", "critical", 40)

    save_result(first, temp_db)
    save_result(second, temp_db)  # same asset, re-scored later

    session = get_session(temp_db)
    rows = session.query(BlastRadiusScore).filter_by(asset_id="srv-10").all()
    session.close()

    assert len(rows) == 1  # still just one row, not two
    assert rows[0].exposure_level == "internet_facing"  # reflects the latest data


def test_score_and_save_returns_result_and_persists(temp_db):
    result = score_and_save("srv-11", "internal_network", "medium", 5, temp_db)

    session = get_session(temp_db)
    row = session.query(BlastRadiusScore).filter_by(asset_id="srv-11").first()
    session.close()

    assert row is not None
    assert row.blast_radius_score == result["blast_radius_score"]
