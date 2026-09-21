"""Tests for resilience_scorer service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.resilience_scorer.blast_radius import calculate_blast_radius
from apps.resilience_scorer.calculator import (
    composite_score,
    safe_pct,
    score_band,
    severity_to_score,
    weighted_risk_score,
)
from apps.resilience_scorer.compute import assemble_score
from apps.resilience_scorer.main import app
from apps.resilience_scorer.models import ResilienceScore, ScoreRequest
from apps.resilience_scorer.repository import list_scores, save_score
from tests.conftest import make_client


@pytest.mark.asyncio
async def test_health_returns_200():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_service_name():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.json()["service"] == "resilience-scorer"


def test_score_band_critical():
    assert score_band(0.0) == "Critical"


def test_score_band_at_risk():
    assert score_band(50.0) == "At Risk"


def test_score_band_moderate():
    assert score_band(70.0) == "Moderate"


def test_score_band_strong():
    assert score_band(85.0) == "Strong"


def test_score_band_resilient():
    assert score_band(100.0) == "Resilient"
    assert score_band(105.0) == "Resilient"


def test_composite_score_calculation():
    # 100% coverage, 100% detection, 100% evidence → 100.0
    assert composite_score(100.0, 100.0, 100.0) == 100.0


def test_composite_score_weighted():
    # 40*0.4 + 60*0.35 + 80*0.25 = 16+21+20 = 57
    assert composite_score(40.0, 60.0, 80.0) == 57.0


def test_safe_pct_normal():
    assert safe_pct(7, 10) == 70.0


def test_safe_pct_zero_denominator():
    assert safe_pct(0, 0) == 0.0


def test_score_request_model():
    req = ScoreRequest(engagement_id="eng-alpha-001", framework_ids=["nist_csf_2.0"])
    assert req.engagement_id == "eng-alpha-001"


def test_resilience_score_model():
    score = ResilienceScore(
        score_id="scr-001",
        engagement_id="eng-alpha-001",
        composite_score=72.5,
        coverage_score=80.0,
        detection_score=70.0,
        evidence_score=60.0,
        band="Moderate",
    )
    assert score.band == "Moderate"


def test_weighted_risk_score_normal_and_clamp():
    assert weighted_risk_score(1.0, 0.1, 25.0) == round(
        1.0 * 10 * 0.5 + 0.1 * 100 * 0.3 + 25.0 * 0.2, 1
    )
    assert weighted_risk_score(10.0, 1.0, 100.0) == 100.0


def test_severity_to_score():
    assert severity_to_score(0) == 0.0
    assert severity_to_score(3) == 60.0
    assert severity_to_score(5) == 100.0
    assert severity_to_score(9) == 100.0
    assert severity_to_score(-1) == 0.0


def test_assemble_score_full():
    score = assemble_score(
        score_id="scr-e2e-001",
        engagement_id="eng-alpha-001",
        statuses={"DE.CM-01": "Met", "DE.AE-02": "Not Met"},
        total_verdicts=2,
        detected_verdicts=1,
        linked_events=1,
        expected_events=2,
    )
    assert score.coverage_score == 50.0
    assert score.detection_score == 50.0
    assert score.evidence_score == 50.0
    assert score.composite_score == 50.0
    assert score.band == "At Risk"


def test_blast_radius_combinations():
    assert calculate_blast_radius("internal", "low", False) == 30.0
    assert calculate_blast_radius("external", "medium", False) == 65.0
    assert calculate_blast_radius("external", "high", True) == 100.0


@pytest.mark.asyncio
async def test_repository_save_and_list_scores(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    score = ResilienceScore(
        score_id="scr-repo-001",
        engagement_id="eng-alpha-001",
        composite_score=45.0,
        coverage_score=40.0,
        detection_score=50.0,
        evidence_score=45.0,
        band="Critical",
    )
    async with db_session_factory() as session:
        saved = await save_score(session, score)
        history = await list_scores(session, "eng-alpha-001")
    assert saved.score_id == "scr-repo-001"
    assert any(s.score_id == "scr-repo-001" for s in history)


@pytest.mark.asyncio
async def test_calculate_score_flow(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "rs-e2e-001"
    verdict_id = f"{engagement_id}-vrd-0000"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'RS', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
                " VALUES (:vid, :e, 'T1078', 'Detected', 1, "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"vid": verdict_id, "e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.CM-01', 'Met', "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO evidence_links "
                "(link_id, control_id, verdict_id, evidence_hash, chain_position)"
                " VALUES ('DE.CM-01:' || :vid, 'DE.CM-01', :vid, "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8', 0)"
            ),
            {"vid": verdict_id},
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/calculate-score",
            json={"engagement_id": engagement_id, "framework_ids": ["nist_csf_2.0"]},
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["composite_score"] == 100.0
        assert body["band"] == "Resilient"

        history = await client.get(f"/api/v1/scores/{engagement_id}")
        assert len(history.json()) == 1


@pytest.mark.asyncio
async def test_blast_radius_and_weighted_risk_endpoints():
    async with make_client(app) as client:
        blast = await client.post(
            "/api/v1/blast-radius",
            json={
                "asset_id": "asset-01",
                "exposure": "external",
                "criticality": "high",
                "internet_facing": True,
            },
        )
        assert blast.json()["blast_radius_score"] == 100.0

        risk = await client.post(
            "/api/v1/weighted-risk",
            json={
                "cve_id": "CVE-2024-0001",
                "cvss": 6.0,
                "epss": 0.5,
                "blast_radius": 50.0,
            },
        )
        body = risk.json()
        assert body["cve_id"] == "CVE-2024-0001"
        assert body["final_score"] == round(
            6.0 * 10 * 0.5 + 0.5 * 100 * 0.3 + 50.0 * 0.2, 1
        )
        assert body["band"] == score_band(
            round(6.0 * 10 * 0.5 + 0.5 * 100 * 0.3 + 50.0 * 0.2, 1)
        )
