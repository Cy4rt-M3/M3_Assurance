"""
Tests for the Threat Intel Integration Pipeline.

These use mocked API responses (unittest.mock) instead of calling the
real NVD/FIRST.org APIs, so tests run instantly, don't need internet,
and don't get rate-limited.

Run with:
    pytest test_threat_intel.py -v
"""

from unittest.mock import patch, Mock

import pytest

from threat_intel_pipeline import (
    is_valid_cve_id,
    get_cvss_score,
    get_epss_score,
    enrich_cve,
    dedupe_cve_ids,
    save_result,
)
from database import ThreatIntel, get_session, init_db


# --- dedupe_cve_ids ---


def test_dedupe_removes_case_insensitive_duplicates():
    result = dedupe_cve_ids(["CVE-2024-3400", "cve-2024-3400", "CVE-2021-44228"])
    assert result == ["CVE-2024-3400", "CVE-2021-44228"]


def test_dedupe_preserves_order():
    result = dedupe_cve_ids(["CVE-2021-44228", "CVE-2024-3400", "CVE-2021-44228"])
    assert result == ["CVE-2021-44228", "CVE-2024-3400"]


def test_dedupe_handles_empty_list():
    assert dedupe_cve_ids([]) == []


def test_dedupe_strips_whitespace():
    result = dedupe_cve_ids([" CVE-2024-3400 ", "CVE-2024-3400"])
    assert result == ["CVE-2024-3400"]


# --- save_result upsert behavior ---


@pytest.fixture
def temp_db(tmp_path):
    """A fresh, throwaway SQLite file per test - doesn't touch your real data."""
    db_path = str(tmp_path / "test_threat_intel.db")
    init_db(db_path)
    return db_path


def test_save_result_creates_one_row_for_new_cve(temp_db):
    result = {
        "cve_id": "CVE-2024-3400",
        "cvss_score": 10.0,
        "severity": "CRITICAL",
        "epss_score": 0.95,
        "epss_percentile": 0.99,
        "status": "ok",
        "error": None,
    }
    save_result(result, temp_db)

    session = get_session(temp_db)
    rows = session.query(ThreatIntel).filter_by(cve_id="CVE-2024-3400").all()
    session.close()

    assert len(rows) == 1
    assert rows[0].cvss_score == 10.0


def test_save_result_updates_existing_row_instead_of_duplicating(temp_db):
    first = {
        "cve_id": "CVE-2024-3400",
        "cvss_score": 10.0,
        "severity": "CRITICAL",
        "epss_score": 0.5,
        "epss_percentile": 0.8,
        "status": "ok",
        "error": None,
    }
    second = {
        "cve_id": "CVE-2024-3400",
        "cvss_score": 10.0,
        "severity": "CRITICAL",
        "epss_score": 0.97,
        "epss_percentile": 0.99,
        "status": "ok",
        "error": None,
    }

    save_result(first, temp_db)
    save_result(second, temp_db)  # same CVE, re-enriched later

    session = get_session(temp_db)
    rows = session.query(ThreatIntel).filter_by(cve_id="CVE-2024-3400").all()
    session.close()

    assert len(rows) == 1  # still just one row, not two
    assert rows[0].epss_score == 0.97  # reflects the latest data


# --- CVE ID validation ---


def test_valid_cve_id_accepted():
    assert is_valid_cve_id("CVE-2024-3400") is True


def test_lowercase_cve_id_accepted():
    assert is_valid_cve_id("cve-2024-3400") is True


def test_invalid_cve_id_rejected():
    assert is_valid_cve_id("NOT-A-REAL-CVE") is False


def test_empty_string_rejected():
    assert is_valid_cve_id("") is False


# --- get_cvss_score, with NVD mocked ---


@patch("threat_intel_pipeline._get_with_retry")
def test_get_cvss_score_parses_v31(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "vulnerabilities": [
            {
                "cve": {
                    "metrics": {
                        "cvssMetricV31": [
                            {"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}
                        ]
                    }
                }
            }
        ]
    }
    mock_get.return_value = mock_response

    result = get_cvss_score("CVE-2024-3400")

    assert result["cvss_score"] == 9.8
    assert result["severity"] == "CRITICAL"
    assert result["error"] is None


@patch("threat_intel_pipeline._get_with_retry")
def test_get_cvss_score_handles_no_data(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {"vulnerabilities": []}
    mock_get.return_value = mock_response

    result = get_cvss_score("CVE-9999-99999")

    assert result["cvss_score"] is None
    assert result["error"] is None  # no data is not an error, just empty


@patch("threat_intel_pipeline._get_with_retry")
def test_get_cvss_score_handles_network_failure(mock_get):
    mock_get.side_effect = RuntimeError("connection failed")

    result = get_cvss_score("CVE-2024-3400")

    assert result["cvss_score"] is None
    assert result["error"] is not None


# --- get_epss_score, with FIRST.org mocked ---


@patch("threat_intel_pipeline._get_with_retry")
def test_get_epss_score_parses_response(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"epss": "0.94231", "percentile": "0.99800"}]
    }
    mock_get.return_value = mock_response

    result = get_epss_score("CVE-2024-3400")

    assert result["epss_score"] == pytest.approx(0.94231)
    assert result["percentile"] == pytest.approx(0.998)
    assert result["error"] is None


# --- enrich_cve, end-to-end with both mocked ---


@patch("threat_intel_pipeline.get_epss_score")
@patch("threat_intel_pipeline.get_cvss_score")
def test_enrich_cve_combines_both_sources(mock_cvss, mock_epss):
    mock_cvss.return_value = {"cvss_score": 10.0, "severity": "CRITICAL", "error": None}
    mock_epss.return_value = {"epss_score": 0.95, "percentile": 0.99, "error": None}

    result = enrich_cve("CVE-2024-3400")

    assert result["cve_id"] == "CVE-2024-3400"
    assert result["cvss_score"] == 10.0
    assert result["epss_score"] == 0.95
    assert result["status"] == "ok"
    assert result["error"] is None


def test_enrich_cve_rejects_invalid_id_without_calling_apis():
    result = enrich_cve("NOT-A-REAL-CVE")

    assert result["status"] == "error"
    assert "Invalid CVE ID format" in result["error"]


@patch("threat_intel_pipeline.get_epss_score")
@patch("threat_intel_pipeline.get_cvss_score")
def test_enrich_cve_reports_partial_failure(mock_cvss, mock_epss):
    mock_cvss.return_value = {"cvss_score": 10.0, "severity": "CRITICAL", "error": None}
    mock_epss.return_value = {
        "epss_score": None,
        "percentile": None,
        "error": "timeout",
    }

    result = enrich_cve("CVE-2024-3400")

    assert result["status"] == "error"
    assert "timeout" in result["error"]
    assert result["cvss_score"] == 10.0  # the part that succeeded is still returned
