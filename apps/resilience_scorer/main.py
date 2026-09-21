"""Resilience Scorer Service — composite score, band, blast radius, risk."""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from apps.control_mapping.repository import get_control_statuses
from apps.evidence_aggregator.repository import (
    count_verdicts,
    get_evidence_summary,
    list_verdicts,
)
from apps.resilience_scorer.blast_radius import calculate_blast_radius
from apps.resilience_scorer.calculator import score_band, weighted_risk_score
from apps.resilience_scorer.compute import assemble_score
from apps.resilience_scorer.models import (
    BlastRadiusRequest,
    BlastRadiusResponse,
    ResilienceScore,
    ScoreRequest,
    WeightedRiskRequest,
    WeightedRiskResponse,
)
from apps.resilience_scorer.repository import list_scores, save_score
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)

app = FastAPI(
    title="Resilience Scorer Service",
    description="Computes composite Resilience Score.",
    version="0.1.0",
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session per request."""
    async with _session_factory() as session:
        yield session


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check for resilience-scorer."""
    db_ok = await check_db(_engine)
    return {
        "service": "resilience-scorer",
        "port": _settings.port_resilience_scorer,
        "db": db_ok,
        "redis": True,
    }


@app.post("/api/v1/calculate-score", response_model=ResilienceScore)
async def calculate_score(
    request: ScoreRequest,
    session: AsyncSession = Depends(get_session),
) -> ResilienceScore:
    """Compute and persist the composite Resilience Score for an engagement."""
    verdicts = await list_verdicts(session, request.engagement_id)
    statuses = await get_control_statuses(session, request.engagement_id)

    total = len(verdicts)
    detected = sum(1 for verdict in verdicts if verdict["outcome"] == "Detected")
    _, unique = await get_evidence_summary(session, request.engagement_id)
    expected = await count_verdicts(session, request.engagement_id)

    history = await list_scores(session, request.engagement_id)
    score_id = f"{request.engagement_id}-scr-{len(history) + 1:04d}"

    score = assemble_score(
        score_id=score_id,
        engagement_id=request.engagement_id,
        statuses=statuses,
        total_verdicts=total,
        detected_verdicts=detected,
        linked_events=unique,
        expected_events=expected,
    )
    return await save_score(session, score)


@app.get("/api/v1/scores/{engagement_id}", response_model=list[ResilienceScore])
async def scores_history(
    engagement_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[ResilienceScore]:
    """Return the resilience score history for an engagement."""
    return await list_scores(session, engagement_id)


@app.post("/api/v1/blast-radius", response_model=BlastRadiusResponse)
async def blast_radius(
    request: BlastRadiusRequest,
) -> BlastRadiusResponse:
    """Calculate a blast radius score for an asset."""
    score = calculate_blast_radius(
        request.exposure,  # type: ignore[arg-type]
        request.criticality,  # type: ignore[arg-type]
        request.internet_facing,
    )
    return BlastRadiusResponse(
        asset_id=request.asset_id,
        blast_radius_score=score,
    )


@app.post("/api/v1/weighted-risk", response_model=WeightedRiskResponse)
async def weighted_risk(
    request: WeightedRiskRequest,
) -> WeightedRiskResponse:
    """Combine CVSS, EPSS and blast radius into a weighted risk score."""
    final_score = weighted_risk_score(request.cvss, request.epss, request.blast_radius)
    return WeightedRiskResponse(
        cve_id=request.cve_id,
        final_score=final_score,
        band=score_band(final_score),
    )
