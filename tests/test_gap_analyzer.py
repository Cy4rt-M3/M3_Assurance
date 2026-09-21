"""Tests for gap_analyzer service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.framework_registry.models import Control
from apps.gap_analyzer import analyzer
from apps.gap_analyzer.main import app
from apps.gap_analyzer.models import GapAnalysis, GapSummary
from apps.gap_analyzer.prioritization import priority_label, sort_by_priority
from apps.gap_analyzer.repository import list_gaps, save_gaps
from tests.conftest import make_client


def _make_gap(analysis_id: str, priority: int) -> GapAnalysis:
    return GapAnalysis(
        analysis_id=analysis_id,
        engagement_id="eng-alpha-001",
        control_id="DE.AE-02",
        gap_type="uncovered_control",
        priority=priority,
        remediation="Deploy detection rule for T1486.",
    )


@pytest.mark.asyncio
async def test_health_returns_200():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_service_name():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.json()["service"] == "gap-analyzer"


def test_priority_label_critical():
    assert priority_label(1) == "Critical"


def test_priority_label_informational():
    assert priority_label(5) == "Informational"


def test_priority_label_unknown():
    assert priority_label(99) == "Unknown"


def test_sort_by_priority_orders_correctly():
    gaps = [_make_gap("g3", 3), _make_gap("g1", 1), _make_gap("g2", 2)]
    result = sort_by_priority(gaps)
    assert [g.analysis_id for g in result] == ["g1", "g2", "g3"]


def test_gap_analysis_model():
    gap = _make_gap("gap-001", 2)
    assert gap.gap_type == "uncovered_control"


def test_gap_summary_model():
    summary = GapSummary(
        engagement_id="eng-alpha-001",
        total_gaps=3,
        critical_gaps=1,
        gaps=[_make_gap("g1", 1)],
    )
    assert summary.critical_gaps == 1


def _control(control_id: str, mapping: list[str]) -> Control:
    return Control(
        control_id=control_id,
        framework_id="nist_csf_2.0",
        category="Detect",
        name=control_id,
        description="Test control",
        attack_mapping=mapping,
    )


def _verdict(verdict_id: str, technique: str, outcome: str, severity: int = 1):
    return {
        "verdict_id": verdict_id,
        "engagement_id": "eng-alpha-001",
        "technique_id": technique,
        "outcome": outcome,
        "severity_id": severity,
        "evidence_hash": "d" * 64,
    }


def test_priority_for_verdict():
    assert analyzer.priority_for_verdict({"severity_id": 5}) == 1
    assert analyzer.priority_for_verdict({"severity_id": 4}) == 1
    assert analyzer.priority_for_verdict({"severity_id": 3}) == 2
    assert analyzer.priority_for_verdict({"severity_id": 2}) == 3
    assert analyzer.priority_for_verdict({}) == 3


def test_remediation_techniques_uses_effective_mapping():
    control = _control("DE.AE-02", ["T1486", "T1490", "Impact"])
    hint = analyzer.remediation_techniques(control, {"T1486", "T1078", "T1490"})
    assert hint == "T1486, T1490"


def test_analyze_uncovered_control_gaps():
    controls = [
        _control("DE.AE-02", ["T1486", "T1490"]),
        _control("DE.CM-01", ["T1078"]),
        _control("RS.MI-01", ["T1486"]),
    ]
    statuses = {
        "DE.AE-02": "Not Met",
        "DE.CM-01": "Partial",
        "RS.MI-01": "Met",
        "GHOST": "Not Met",
    }
    gaps = analyzer.analyze(
        "eng-alpha-001", statuses, [_verdict("v1", "T1486", "Detected")], controls
    )
    uncovered = [g for g in gaps if g.gap_type == "uncovered_control"]
    assert len(uncovered) == 2
    by_id = {g.control_id: g for g in uncovered}
    assert by_id["DE.AE-02"].priority == 1
    assert "Deploy detection or compensating control" in by_id["DE.AE-02"].remediation
    assert by_id["DE.CM-01"].priority == 3
    assert "Complete validation" in by_id["DE.CM-01"].remediation
    assert "GHOST" not in by_id


def test_analyze_verdict_gaps_and_dedup():
    controls = [
        _control("DE.AE-02", ["T1486", "T1490"]),
        _control("DE.CM-01", ["T1078"]),
    ]
    verdicts = [
        _verdict("v1", "T1486", "Missed", severity=4),
        _verdict("v2", "T1486", "Missed", severity=1),
        _verdict("v3", "T1078", "No Data"),
    ]
    gaps = analyzer.analyze("eng-alpha-001", {}, verdicts, controls)

    missed = [g for g in gaps if g.gap_type == "missed_detection"]
    assert len(missed) == 1
    assert missed[0].control_id == "DE.AE-02"
    assert missed[0].priority == 1
    assert "T1486" in missed[0].remediation

    evidence = [g for g in gaps if g.gap_type == "evidence_gap"]
    assert len(evidence) == 1
    assert evidence[0].control_id == "DE.CM-01"
    assert evidence[0].priority == 3


def test_analyze_empty_inputs():
    assert analyzer.analyze("eng-alpha-001", {}, [], []) == []
    assert (
        analyzer.analyze("eng-alpha-001", {}, [], [_control("DE.AE-02", ["T1486"])])
        == []
    )


def test_analyze_verdict_without_mapped_control():
    verdicts = [_verdict("v1", "T9999", "No Data")]
    gaps = analyzer.analyze(
        "eng-alpha-001", {}, verdicts, [_control("DE.AE-02", ["T1486"])]
    )
    assert gaps == []


@pytest.mark.asyncio
async def test_repository_save_and_list_gaps(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    gap = GapAnalysis(
        analysis_id="gap-repo-001",
        engagement_id="eng-alpha-001",
        control_id="DE.AE-02",
        gap_type="uncovered_control",
        priority=2,
        remediation="Upgrade monitoring.",
    )
    async with db_session_factory() as session:
        saved = await save_gaps(session, [gap])
        again = await save_gaps(session, [gap])
        listed = await list_gaps(session, "eng-alpha-001")
    assert saved[0].analysis_id == "gap-repo-001"
    assert again[0].analysis_id == "gap-repo-001"
    assert any(g.analysis_id == "gap-repo-001" for g in listed)


@pytest.mark.asyncio
async def test_analyze_gaps_endpoint(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "gap-e2e-001"
    verdict_hash = "a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'Gap', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
                " VALUES (:vid, :e, 'T1078', 'Missed', 4, :h)"
            ),
            {"vid": f"{engagement_id}-vrd-0000", "e": engagement_id, "h": verdict_hash},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses "
                "(engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.CM-01', 'Not Met', :h)"
            ),
            {"e": engagement_id, "h": verdict_hash},
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/analyze-gaps",
            json={"engagement_id": engagement_id, "framework_ids": ["nist_csf_2.0"]},
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["engagement_id"] == engagement_id
        assert body["total_gaps"] == 2
        assert body["critical_gaps"] == 2

        listed = await client.get(f"/api/v1/gaps/{engagement_id}")
        assert len(listed.json()) == 2


@pytest.mark.asyncio
async def test_analyze_gaps_engagement_not_found():
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/analyze-gaps",
            json={"engagement_id": "no-eng", "framework_ids": []},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_gaps_endpoint_empty():
    async with make_client(app) as client:
        resp = await client.get("/api/v1/gaps/empty-eng")
    assert resp.json() == []
