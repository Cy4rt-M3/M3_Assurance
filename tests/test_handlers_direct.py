"""Direct async-handler tests.

HTTP (ASGI) requests don't capture lines after ``await`` in coverage, so the
handlers are called directly with a real session to trace every branch.
"""

from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.control_mapping.main import control_statuses, map_controls
from apps.control_mapping.models import ControlMappingRequest
from apps.evidence_aggregator import repository as evidence_repository
from apps.evidence_aggregator.main import (
    create_link,
    evidence_summary,
    ingest_ocsf,
    verdict_detail,
)
from apps.evidence_aggregator.models import EvidenceLink, IngestRequest
from apps.gap_analyzer.main import analyze_gaps
from apps.gap_analyzer.models import GapRequest
from apps.report_generator.main import (
    _latest_score,  # type: ignore[reportPrivateUsage]
    generate_report,
    report_detail,
)
from apps.report_generator.models import ReportRequest
from apps.report_publisher.main import publish
from apps.report_publisher.models import DeliveryRequest
from apps.resilience_scorer.main import calculate_score
from apps.resilience_scorer.models import ResilienceScore, ScoreRequest

_HASH = "a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8"


async def _seed_engagement(session: AsyncSession, engagement_id: str) -> None:
    await session.execute(
        text(
            "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
            "VALUES (:e, 'Dir', 'CyArt', ARRAY['nist_csf_2.0'])"
            " ON CONFLICT (engagement_id) DO NOTHING"
        ),
        {"e": engagement_id},
    )
    await session.commit()


async def _seed_verdict(
    session: AsyncSession,
    engagement_id: str,
    technique: str,
    outcome: str,
    index: int = 0,
) -> str:
    verdict_id = f"{engagement_id}-vrd-{index:04d}"
    await session.execute(
        text(
            "INSERT INTO verdicts "
            "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
            " VALUES (:vid, :e, :t, :o, 1, :h)"
        ),
        {
            "vid": verdict_id,
            "e": engagement_id,
            "t": technique,
            "o": outcome,
            "h": _HASH,
        },
    )
    await session.commit()
    return verdict_id


@pytest.mark.asyncio
async def test_map_controls_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-cm-001"
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        await _seed_verdict(session, engagement_id, "T1486", "Detected")
        await _seed_verdict(session, engagement_id, "T1490", "Missed", index=1)
        request = ControlMappingRequest(
            verdict_id=f"{engagement_id}-vrd-0000",
            framework_ids=["nist_csf_2.0"],
            engagement_id=engagement_id,
        )
        response = await map_controls(request, session)
    assert response.control_statuses["DE.AE-02"] == "Not Met"
    assert response.coverage_pct == 0.0
    assert len(response.framework_ids) == 1
    async with db_session_factory() as session:
        links = await evidence_repository.get_evidence_links(session)
    assert any(
        link.control_id == "DE.AE-02" and link.verdict_id.startswith("dir-cm-001")
        for link in links
    )


@pytest.mark.asyncio
async def test_map_controls_verdict_missing_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        request = ControlMappingRequest(
            verdict_id="no-such-verdict",
            framework_ids=["nist_csf_2.0"],
            engagement_id="dir-cm-002",
        )
        with pytest.raises(HTTPException) as exc:
            await map_controls(request, session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_map_controls_engagement_missing_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-cm-003"
    async with db_session_factory() as session:
        await _seed_verdict(session, engagement_id, "T1078", "Detected")
        request = ControlMappingRequest(
            verdict_id=f"{engagement_id}-vrd-0000",
            framework_ids=["nist_csf_2.0"],
            engagement_id="dir-no-eng",
        )
        with pytest.raises(HTTPException) as exc:
            await map_controls(request, session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_control_statuses_handler_missing_engagement(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-st-001"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status) "
                "VALUES (:e, 'DE.CM-01', 'Met')"
            ),
            {"e": engagement_id},
        )
        await session.commit()
        response = await control_statuses(engagement_id, session)
    assert response.control_statuses["DE.CM-01"] == "Met"
    assert response.framework_ids == []


@pytest.mark.asyncio
async def test_ingest_ocsf_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-ing-001"
    events: list[dict[str, Any]] = [
        {
            "class_uid": 4001,
            "disposition": "Allowed",
            "attack": {"technique_uid": "T1486"},
        },
        {
            "class_uid": 4001,
            "disposition": "Missed",
            "attack": {"technique_uid": "T1078"},
        },
    ]
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        payload = IngestRequest(
            engagement_id=engagement_id,
            name="Dir",
            organization="CyArt",
            frameworks=["nist_csf_2.0"],
            events=events,
        )
        first = await ingest_ocsf(payload, session)
        second = await ingest_ocsf(payload, session)
    assert first.ingested == 2
    assert second.ingested == 0
    assert first.verdict_ids == [
        f"{engagement_id}-vrd-0000",
        f"{engagement_id}-vrd-0001",
    ]


@pytest.mark.asyncio
async def test_create_link_duplicate_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    link = EvidenceLink(
        link_id="dir-link-001",
        control_id="DE.CM-01",
        verdict_id="dir-vrd-001",
        evidence_hash=_HASH,
        chain_position=0,
    )
    async with db_session_factory() as session:
        created = await create_link(link, session)
        found = await evidence_repository.get_evidence_link(session, "dir-link-001")
        missing = await evidence_repository.get_evidence_link(session, "ghost")
        with pytest.raises(HTTPException) as exc:
            await create_link(link, session)
    assert created.link_id == "dir-link-001"
    assert found is not None and found.control_id == "DE.CM-01"
    assert missing is None
    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_evidence_summary_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        summary = await evidence_summary("dir-sum-001", expected=0, session=session)
        explicit = await evidence_summary("dir-sum-001", expected=1, session=session)
    assert summary.total_links == 0
    assert summary.completeness_pct == 0.0
    assert explicit.completeness_pct == 0.0


@pytest.mark.asyncio
async def test_verdict_detail_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-vd-001"
    async with db_session_factory() as session:
        verdict_id = await _seed_verdict(session, engagement_id, "T1078", "Detected")
        found = await verdict_detail(verdict_id, session)
        with pytest.raises(HTTPException) as exc:
            await verdict_detail("no-such-verdict", session)
    assert found["technique_id"] == "T1078"
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_repository_get_engagement_and_verdict_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-repo-001"
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        verdict_id = await _seed_verdict(session, engagement_id, "T1078", "Partial")
        engagement = await evidence_repository.get_engagement(session, engagement_id)
        missing_eng = await evidence_repository.get_engagement(session, "ghost")
        verdict = await evidence_repository.get_verdict(session, verdict_id)
        missing_vrd = await evidence_repository.get_verdict(session, "ghost")
    assert engagement is not None
    assert engagement["frameworks"] == ["nist_csf_2.0"]
    assert missing_eng is None
    assert verdict is not None
    assert verdict["outcome"] == "Partial"
    assert missing_vrd is None


@pytest.mark.asyncio
async def test_report_generator_latest_score_default_and_present():
    default = _latest_score([])
    assert default.score_id == "unset"
    score = ResilienceScore(
        score_id="s1",
        engagement_id="dir",
        composite_score=30.0,
        coverage_score=30.0,
        detection_score=30.0,
        evidence_score=30.0,
        band="Critical",
    )
    assert _latest_score([score]).score_id == "s1"


@pytest.mark.asyncio
async def test_generate_report_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-rg-001"
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        await _seed_verdict(session, engagement_id, "T1486", "Detected")
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.AE-02', 'Met', :h)"
            ),
            {"e": engagement_id, "h": _HASH},
        )
        await session.commit()
        request = ReportRequest(
            engagement_id=engagement_id,
            framework_ids=["nist_csf_2.0"],
            format="html",
        )
        report = await generate_report(request, session)
        missing_request = ReportRequest(
            engagement_id="no-eng", framework_ids=[], format="html"
        )
        with pytest.raises(HTTPException) as exc:
            await generate_report(missing_request, session)
        found = await report_detail(report.report_id, session)
        with pytest.raises(HTTPException) as not_found:
            await report_detail("ghost", session)
    assert report.report_id.startswith(engagement_id)
    assert len(report.content_hash) == 64
    assert found.report_id == report.report_id
    assert exc.value.status_code == 404
    assert not_found.value.status_code == 404


@pytest.mark.asyncio
async def test_publish_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO reports "
                "(report_id, engagement_id, framework_ids, score, format, content_hash)"
                " VALUES ('dir-rpt-001', 'dir-pub-001', ARRAY['nist_csf_2.0'], 60.0, 'html', :h)"
            ),
            {"h": _HASH},
        )
        await session.commit()

        ok = await publish(
            DeliveryRequest(
                report_id="dir-rpt-001", channel="download", recipient="a@b.c"
            ),
            session,
        )
        failed = await publish(
            DeliveryRequest(
                report_id="dir-rpt-001", channel="webhook", recipient="http://x"
            ),
            session,
        )
        with pytest.raises(HTTPException) as missing:
            await publish(
                DeliveryRequest(report_id="nope", channel="email", recipient="a@b.c"),
                session,
            )
        with pytest.raises(HTTPException) as unsupported:
            await publish(
                DeliveryRequest(
                    report_id="dir-rpt-001", channel="fax", recipient="a@b.c"
                ),
                session,
            )
    assert ok.status == "delivered"
    assert ok.delivery_id == "dir-rpt-001-del-001"
    assert failed.status == "failed"
    assert failed.delivery_id == "dir-rpt-001-del-002"
    assert missing.value.status_code == 404
    assert unsupported.value.status_code == 422


@pytest.mark.asyncio
async def test_calculate_score_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-rs-001"
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        verdict_id = await _seed_verdict(session, engagement_id, "T1078", "Detected")
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.CM-01', 'Met', :h)"
            ),
            {"e": engagement_id, "h": _HASH},
        )
        await session.execute(
            text(
                "INSERT INTO evidence_links (link_id, control_id, verdict_id, evidence_hash, chain_position) "
                "VALUES ('DE.CM-01:' || :vid, 'DE.CM-01', :vid, :h, 0)"
            ),
            {"vid": verdict_id, "h": _HASH},
        )
        await session.commit()
        score = await calculate_score(
            ScoreRequest(engagement_id=engagement_id, framework_ids=["nist_csf_2.0"]),
            session,
        )
    assert score.score_id == f"{engagement_id}-scr-0001"
    assert score.composite_score == 100.0
    assert score.band == "Resilient"


@pytest.mark.asyncio
async def test_analyze_gaps_handler_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "dir-gap-001"
    async with db_session_factory() as session:
        await _seed_engagement(session, engagement_id)
        await _seed_verdict(session, engagement_id, "T1078", "Missed")
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status) "
                "VALUES (:e, 'DE.CM-01', 'Not Met')"
            ),
            {"e": engagement_id},
        )
        await session.commit()
        request = GapRequest(
            engagement_id=engagement_id, framework_ids=["nist_csf_2.0"]
        )
        summary = await analyze_gaps(request, session)
        with pytest.raises(HTTPException) as exc:
            await analyze_gaps(
                GapRequest(engagement_id="no-eng", framework_ids=[]), session
            )
    assert summary.total_gaps >= 1
    assert exc.value.status_code == 404
