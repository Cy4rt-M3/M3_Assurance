"""Tests for report_generator service."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.report_generator import generator
from apps.report_generator.main import (
    _build_report,  # type: ignore[reportPrivateUsage]
    _download_response,  # type: ignore[reportPrivateUsage]
    _latest_score,  # type: ignore[reportPrivateUsage]
    _render_payload,  # type: ignore[reportPrivateUsage]
    _require_engagement,  # type: ignore[reportPrivateUsage]
    app,
    generate_report,
    report_detail,
    report_download,
)
from apps.report_generator.models import Report, ReportRequest
from apps.report_generator.repository import (
    get_report,
    get_report_content,
    list_reports,
    save_report,
)
from apps.resilience_scorer.models import ResilienceScore
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
    assert resp.json()["service"] == "report-generator"


def test_report_request_default_format():
    req = ReportRequest(engagement_id="eng-alpha-001", framework_ids=["nist_csf_2.0"])
    assert req.format == "pdf"


def test_report_request_html_format():
    req = ReportRequest(
        engagement_id="eng-alpha-001",
        framework_ids=["nist_csf_2.0"],
        format="html",
    )
    assert req.format == "html"


def test_report_model():
    report = Report(
        report_id="rpt-001",
        engagement_id="eng-alpha-001",
        framework_ids=["nist_csf_2.0", "iso_27001_2022"],
        composite_score=78.5,
        format="pdf",
        content_hash="a" * 64,
    )
    assert len(report.framework_ids) == 2


def _score(band: str) -> ResilienceScore:
    return ResilienceScore(
        score_id="s1",
        engagement_id="eng-alpha-001",
        composite_score=55.0,
        coverage_score=50.0,
        detection_score=60.0,
        evidence_score=55.0,
        band=band,
    )


def _control() -> Control:
    return Control(
        control_id="DE.AE-02",
        framework_id="nist_csf_2.0",
        category="Detect",
        name="<script>Anomalies</script>",
        description="Detect anomalies",
        attack_mapping=["T1486"],
    )


def _gap() -> GapAnalysis:
    return GapAnalysis(
        analysis_id="g1",
        engagement_id="eng-alpha-001",
        control_id="DE.AE-02",
        gap_type="uncovered_control",
        priority=1,
        remediation="Deploy detection for <b>T1486</b>",
    )


def test_content_hash_deterministic_and_len():
    assert generator.content_hash("hello") == generator.content_hash("hello")
    assert len(generator.content_hash("hello")) == 64


def test_content_hash_bytes():
    import hashlib

    assert generator.content_hash_bytes(b"hello") == hashlib.sha256(b"hello").hexdigest()
    assert generator.content_hash_bytes(b"hello world") != generator.content_hash(
        "hello"
    )
    assert len(generator.content_hash_bytes(b"hello")) == 64


def _engagement() -> dict[str, Any]:
    return {
        "engagement_id": "eng-alpha-001",
        "name": "Alpha",
        "organization": "Org",
        "frameworks": ["nist_csf_2.0"],
    }


def test_require_engagement_passes_and_raises():
    from fastapi import HTTPException

    assert _require_engagement(_engagement())["engagement_id"] == "eng-alpha-001"
    with pytest.raises(HTTPException) as excinfo:
        _require_engagement(None)
    assert excinfo.value.status_code == 404


def test_latest_score_fallback_zeroed_band():
    assert _latest_score([]).band == "Critical"
    assert _latest_score([_score("Strong")]).composite_score == 55.0


def test_render_payload_html_and_pdf():
    html_payload, html_hash = _render_payload(
        "html",
        _engagement(),
        {"DE.AE-02": "Met"},
        [_control()],
        [{"verdict_id": "v1", "technique_id": "T1486", "outcome": "Detected"}],
        _score("Strong"),
        [_gap()],
        report_id="eng-alpha-001-rpt-0001",
        generated_at=datetime(2026, 9, 20, tzinfo=UTC),
    )
    assert html_payload.startswith(b"<!DOCTYPE html>")
    assert html_hash == generator.content_hash(html_payload.decode("utf-8"))

    pdf_payload, pdf_hash = _render_payload(
        "pdf",
        _engagement(),
        {"DE.AE-02": "Met"},
        [_control()],
        [{"verdict_id": "v1", "technique_id": "T1486", "outcome": "Detected"}],
        _score("Strong"),
        [_gap()],
        report_id="eng-alpha-001-rpt-0001",
        generated_at=datetime(2026, 9, 20, tzinfo=UTC),
    )
    assert pdf_payload.startswith(b"%PDF-")
    assert pdf_hash == generator.content_hash_bytes(pdf_payload)


def test_build_report_receives_explicit_id_and_format():
    report = _build_report(
        "eng-alpha-001-rpt-0003",
        "eng-alpha-001",
        ["nist_csf_2.0"],
        _score("Strong"),
        "a" * 64,
        "html",
    )
    assert report.report_id == "eng-alpha-001-rpt-0003"
    assert report.format == "html"
    assert report.content_hash == "a" * 64
    assert report.composite_score == 55.0
    assert report.format == "html"
    assert report.composite_score == 55.0
    assert report.content_hash == "a" * 64


def test_download_response_media_and_disposition():
    pdf_response = _download_response("rpt-dl-001", "pdf", b"%PDF-probe")
    assert pdf_response.media_type == "application/pdf"
    assert 'filename="rpt-dl-001.pdf"' in pdf_response.headers["content-disposition"]

    html_response = _download_response("rpt-dl-002", "html", b"<!DOCTYPE html>")
    assert html_response.media_type == "text/html"
    assert 'filename="rpt-dl-002.html"' in html_response.headers["content-disposition"]


def test_render_score_all_bands():
    from apps.report_generator.generator import (  # type: ignore[reportPrivateUsage]
        _render_score,  # type: ignore[reportPrivateUsage]
    )

    for band in ("Critical", "At Risk", "Moderate", "Strong", "Resilient", "Weird"):
        html = _render_score(_score(band))
        assert band in html
        assert "55.0" in html
    assert "background:#111827" in _render_score(_score("Weird"))


# type: ignore[reportPrivateUsage]
def test_render_controls_escapes_and_defaults():
    from apps.report_generator.generator import (
        _render_controls,  # type: ignore[reportPrivateUsage]
    )

    other = Control(
        control_id="RS.MI-01",
        framework_id="nist_csf_2.0",
        category="Respond",
        name="Containment",
        description="Contain threats",
        attack_mapping=["T1490"],
    )
    html = _render_controls({"DE.AE-02": "Met"}, [_control(), other])
    assert "&lt;script&gt;Anomalies&lt;/script&gt;" in html
    assert "Not evaluated" in html
    assert "DE.AE-02" in html  # type: ignore[reportPrivateUsage]


def test_render_gaps():
    from apps.report_generator.generator import (
        _render_gaps,  # type: ignore[reportPrivateUsage]
    )

    html = _render_gaps([_gap()])
    assert "uncovered_control" in html  # type: ignore[reportPrivateUsage]
    assert "&lt;b&gt;T1486&lt;/b&gt;" in html
    assert "Total gaps: 1" in html


def test_render_verdicts():
    from apps.report_generator.generator import (
        _render_verdicts,  # type: ignore[reportPrivateUsage]
    )

    html = _render_verdicts(
        [{"verdict_id": "v1", "technique_id": "T1486", "outcome": "Detected"}]
    )
    assert "T1486" in html
    assert "Detected" in html


def test_render_report_assembles_document():
    html = generator.render_report(
        {
            "engagement_id": "eng-alpha-001",
            "name": "Alpha",
            "organization": "Org <Co>",
            "frameworks": ["nist_csf_2.0"],
        },
        {"DE.AE-02": "Met"},
        [_control()],
        [{"verdict_id": "v1", "technique_id": "T1486", "outcome": "Detected"}],
        _score("Strong"),
        [_gap()],
    )
    assert html.startswith("<!DOCTYPE html>")
    assert "<h1>Compliance Assessment Report</h1>" in html
    assert "eng-alpha-001" in html
    assert "Org &lt;Co&gt;" in html
    assert "nist_csf_2.0" in html
    assert "CyArt Tech LLP — M3 Assurance" in html


@pytest.mark.asyncio
async def test_report_repository_save_get_list(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    report = Report(
        report_id="rpt-repo-001",
        engagement_id="eng-alpha-001",
        framework_ids=["nist_csf_2.0"],
        composite_score=77.0,
        format="html",
        content_hash="c" * 64,
    )
    async with db_session_factory() as session:
        saved = await save_report(session, report)
        found = await get_report(session, "rpt-repo-001")
        missing = await get_report(session, "rpt-nope")
        listed = await list_reports(session, "eng-alpha-001")
    assert saved.report_id == "rpt-repo-001"
    assert found is not None and found.composite_score == 77.0
    assert missing is None
    assert any(r.report_id == "rpt-repo-001" for r in listed)


@pytest.mark.asyncio
async def test_report_repository_content_round_trip(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    report = Report(
        report_id="rpt-repo-pdf",
        engagement_id="eng-alpha-001",
        framework_ids=["nist_csf_2.0"],
        composite_score=80.0,
        format="pdf",
        content_hash="d" * 64,
    )
    payload = b"%PDF-1.7 fake report bytes"
    async with db_session_factory() as session:
        await save_report(session, report, content=payload)
        no_content_report = Report(
            report_id="rpt-repo-null",
            engagement_id="eng-alpha-001",
            framework_ids=["nist_csf_2.0"],
            composite_score=81.0,
            format="html",
            content_hash="e" * 64,
        )
        await save_report(session, no_content_report)
        stored = await get_report_content(session, "rpt-repo-pdf")
        missing = await get_report_content(session, "nope")
        no_content = await get_report_content(session, "rpt-repo-null")
    assert stored == ("pdf", b"%PDF-1.7 fake report bytes")
    assert missing is None
    assert no_content is None


@pytest.mark.asyncio
async def test_generate_report_endpoint(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "rg-e2e-001"
    verdict_id = f"{engagement_id}-vrd-0000"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'RG', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
                " VALUES (:vid, :e, 'T1486', 'Detected', 2, "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"vid": verdict_id, "e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses "
                "(engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.AE-02', 'Met', "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO resilience_scores "
                "(score_id, engagement_id, composite, coverage, detection, evidence, band) "
                "VALUES (:sid, :e, 60.0, 60.0, 60.0, 60.0, 'Moderate')"
            ),
            {"sid": f"{engagement_id}-scr-0001", "e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO gap_analyses "
                "(analysis_id, engagement_id, control_id, gap_type, priority, remediation) "
                "VALUES (:aid, :e, 'DE.AE-02', 'uncovered_control', 2, 'Fix it')"
            ),
            {"aid": f"{engagement_id}-gap-0000", "e": engagement_id},
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/generate-report",
            json={
                "engagement_id": engagement_id,
                "framework_ids": ["nist_csf_2.0"],
                "format": "html",
            },
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["report_id"].startswith(engagement_id)
        assert body["format"] == "html"
        assert len(body["content_hash"]) == 64
        assert body["composite_score"] == 60.0

        detail = await client.get(f"/api/v1/reports/{body['report_id']}")
        assert detail.status_code == 200
        assert detail.json()["content_hash"] == body["content_hash"]

        missing = await client.get("/api/v1/reports/nope")
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_generate_report_pdf_and_download(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "rg-pdf-001"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'RG', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses "
                "(engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.AE-02', 'Met', "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO resilience_scores "
                "(score_id, engagement_id, composite, coverage, detection, evidence, band) "
                "VALUES (:sid, :e, 60.0, 60.0, 60.0, 60.0, 'Moderate')"
            ),
            {"sid": f"{engagement_id}-scr-0001", "e": engagement_id},
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/generate-report",
            json={
                "engagement_id": engagement_id,
                "framework_ids": ["nist_csf_2.0"],
                "format": "pdf",
            },
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["format"] == "pdf"
        assert body["composite_score"] == 60.0

        detail = await client.get(f"/api/v1/reports/{body['report_id']}")
        assert detail.status_code == 200
        assert detail.headers["content-type"].startswith("application/json")

        download = await client.get(
            f"/api/v1/reports/{body['report_id']}/download"
        )
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("application/pdf")
        assert "attachment" in download.headers["content-disposition"]
        assert download.content.startswith(b"%PDF-")
        assert generator.content_hash_bytes(download.content) == body["content_hash"]

        html_generate = await client.post(
            "/api/v1/generate-report",
            json={
                "engagement_id": engagement_id,
                "framework_ids": ["nist_csf_2.0"],
                "format": "html",
            },
        )
        html_id = html_generate.json()["report_id"]
        html_download = await client.get(f"/api/v1/reports/{html_id}/download")
        assert html_download.status_code == 200
        assert html_download.headers["content-type"].startswith("text/html")
        assert html_download.content.startswith(b"<!DOCTYPE html>")
        assert generator.content_hash_bytes(html_download.content) == html_generate.json()[
            "content_hash"
        ]

        missing = await client.get("/api/v1/reports/nope/download")
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_generate_and_download_direct(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    """Exercise the handlers directly (no ASGI) to trace every line."""
    engagement_id = "rg-direct-001"
    verdict_id = f"{engagement_id}-vrd-0000"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'RG', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
                " VALUES (:vid, :e, 'T1486', 'Detected', 2, "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"vid": verdict_id, "e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses "
                "(engagement_id, control_id, status, evidence_hash) "
                "VALUES (:e, 'DE.AE-02', 'Met', "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO resilience_scores "
                "(score_id, engagement_id, composite, coverage, detection, evidence, band) "
                "VALUES (:sid, :e, 62.0, 60.0, 65.0, 60.0, 'Moderate')"
            ),
            {"sid": f"{engagement_id}-scr-0001", "e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO gap_analyses "
                "(analysis_id, engagement_id, control_id, gap_type, priority, remediation) "
                "VALUES (:aid, :e, 'DE.AE-02', 'uncovered_control', 1, 'Fix it')"
            ),
            {"aid": f"{engagement_id}-gap-0000", "e": engagement_id},
        )
        await session.commit()

        request = ReportRequest(
            engagement_id=engagement_id, framework_ids=["nist_csf_2.0"], format="pdf"
        )
        report = await generate_report(request, session)
        assert report.report_id.startswith(engagement_id)
        assert report.format == "pdf"
        assert report.composite_score == 62.0
        assert len(report.content_hash) == 64

        stored = await get_report_content(session, report.report_id)
        assert stored is not None
        stored_format, stored_content = stored
        assert stored_format == "pdf"
        assert stored_content.startswith(b"%PDF-")
        assert generator.content_hash_bytes(stored_content) == report.content_hash

        response = await report_download(report.report_id, session)
        assert response.media_type == "application/pdf"
        assert response.body == stored_content

        with pytest.raises(HTTPException) as excinfo:
            await report_download("no-such-report", session)
        assert excinfo.value.status_code == 404

        detail_report = await report_detail(report.report_id, session)
        assert detail_report.report_id == report.report_id

        with pytest.raises(HTTPException) as excinfo:
            await report_detail("no-such-report", session)
        assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_generate_report_engagement_not_found():
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/generate-report",
            json={"engagement_id": "no-eng", "framework_ids": [], "format": "html"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reports_for_engagement_lists(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "rg-list-001"
    async with db_session_factory() as session:
        await save_report(
            session,
            Report(
                report_id=f"{engagement_id}-rpt-0001",
                engagement_id=engagement_id,
                framework_ids=["nist_csf_2.0"],
                composite_score=88.5,
                format="html",
                content_hash="a" * 64,
            ),
        )
        await save_report(
            session,
            Report(
                report_id=f"{engagement_id}-rpt-0002",
                engagement_id=engagement_id,
                framework_ids=["iso_27001_2022"],
                composite_score=91.0,
                format="html",
                content_hash="b" * 64,
            ),
        )

    async with make_client(app) as client:
        resp = await client.get(
            "/api/v1/reports", params={"engagement_id": engagement_id}
        )
        assert resp.status_code == 200
        reports = resp.json()
        assert len(reports) == 2
        assert {item["report_id"] for item in reports} == {
            f"{engagement_id}-rpt-0001",
            f"{engagement_id}-rpt-0002",
        }

        empty = await client.get("/api/v1/reports", params={"engagement_id": "none"})
        assert empty.status_code == 200
        assert empty.json() == []
