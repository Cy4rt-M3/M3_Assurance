"""Report Generator Service — produces compliance reports."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from apps.control_mapping.repository import (
    get_control_statuses,
    list_controls_by_id,
)
from apps.evidence_aggregator import repository as evidence_repository
from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.gap_analyzer.repository import list_gaps
from apps.report_generator import generator, payload, pdf_report
from apps.report_generator.models import Report, ReportRequest
from apps.report_generator.repository import (
    get_report,
    get_report_content,
    list_reports,
    save_report,
)
from apps.resilience_scorer.models import ResilienceScore
from apps.resilience_scorer.repository import list_scores
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)

app = FastAPI(
    title="Report Generator Service",
    description="Generates PDF/HTML compliance reports for all supported frameworks.",
    version="0.1.0",
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session per request."""
    async with _session_factory() as session:
        yield session


def _latest_score(scores: list[ResilienceScore]) -> ResilienceScore:
    """Pick the most recent score, or a zeroed default when none exists."""
    if scores:
        return scores[0]
    return ResilienceScore(
        score_id="unset",
        engagement_id="unset",
        composite_score=0.0,
        coverage_score=0.0,
        detection_score=0.0,
        evidence_score=0.0,
        band="Critical",
    )


def _require_engagement(engagement: dict[str, Any] | None) -> dict[str, Any]:
    """Raise 404 unless the engagement exists (thin, testable guard)."""
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return engagement


def _render_payload(
    request_format: str,
    engagement: dict[str, Any],
    statuses: dict[str, str],
    controls: list[Control],
    verdicts: list[dict[str, Any]],
    score: ResilienceScore,
    gaps: list[GapAnalysis],
    report_id: str,
    generated_at: datetime,
) -> tuple[bytes, str]:
    """Render the payload and content hash for the requested format."""
    if request_format == "html":
        content = generator.render_report(
            engagement, statuses, controls, verdicts, score, gaps
        )
        return content.encode("utf-8"), generator.content_hash(content)
    data = payload.build_report_data(
        engagement=engagement,
        score=score,
        statuses=statuses,
        controls=controls,
        verdicts=verdicts,
        gaps=gaps,
        report_id=report_id,
        generated_at=generated_at,
    )
    report_pdf = pdf_report.report_pdf_bytes(data)
    return report_pdf, generator.content_hash_bytes(report_pdf)


def _build_report(
    report_id: str,
    engagement_id: str,
    framework_ids: list[str],
    score: ResilienceScore,
    content_hash: str,
    request_format: str,
) -> Report:
    """Assemble a Report row from the generated payload metadata."""
    return Report(
        report_id=report_id,
        engagement_id=engagement_id,
        framework_ids=framework_ids,
        composite_score=score.composite_score,
        format=request_format,
        content_hash=content_hash,
    )


def _download_response(
    report_id: str,
    report_format: str,
    content: bytes,
) -> Response:
    """Wrap a stored payload as an attachment download response."""
    if report_format == "html":
        media_type = "text/html"
        extension = "html"
    else:
        media_type = "application/pdf"
        extension = "pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{report_id}.{extension}"'
    }
    return Response(content=content, media_type=media_type, headers=headers)


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check for report-generator."""
    db_ok = await check_db(_engine)
    return {
        "service": "report-generator",
        "port": _settings.port_report_generator,
        "db": db_ok,
        "redis": True,
    }


@app.post("/api/v1/generate-report", response_model=Report)
async def generate_report(
    request: ReportRequest,
    session: AsyncSession = Depends(get_session),
) -> Report:
    """Generate and persist a compliance report for an engagement."""
    engagement = _require_engagement(
        await evidence_repository.get_engagement(session, request.engagement_id)
    )

    statuses = await get_control_statuses(session, request.engagement_id)
    controls = await list_controls_by_id(session, list(statuses))
    verdicts = await evidence_repository.list_verdicts(session, request.engagement_id)
    score = _latest_score(await list_scores(session, request.engagement_id))
    gaps = await list_gaps(session, request.engagement_id)

    history = await list_reports(session, request.engagement_id)
    report_id = f"{request.engagement_id}-rpt-{len(history) + 1:04d}"
    payload, content_hash = _render_payload(
        request.format,
        engagement,
        statuses,
        controls,
        verdicts,
        score,
        gaps,
        report_id=report_id,
        generated_at=datetime.now(UTC),
    )
    report = _build_report(
        report_id,
        request.engagement_id,
        request.framework_ids,
        score,
        content_hash,
        request.format,
    )
    return await save_report(session, report, content=payload)


@app.get("/api/v1/reports", response_model=list[Report])
async def reports_for_engagement(
    engagement_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[Report]:
    """Return all stored reports for an engagement, newest first."""
    return await list_reports(session, engagement_id)


@app.get("/api/v1/reports/{report_id}", response_model=Report)
async def report_detail(
    report_id: str,
    session: AsyncSession = Depends(get_session),
) -> Report:
    """Return a stored report row by id."""
    report = await get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return report


@app.get("/api/v1/reports/{report_id}/download")
async def report_download(
    report_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Stream the rendered report payload (PDF or HTML) for download."""
    row = await get_report_content(session, report_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    report_format, content = row
    return _download_response(report_id, report_format, content)
