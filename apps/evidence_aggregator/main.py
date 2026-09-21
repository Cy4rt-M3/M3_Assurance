"""Evidence Aggregator Service — collects, validates and deduplicates evidence."""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.evidence_aggregator.chain_validator import completeness_pct
from apps.evidence_aggregator.models import (
    EvidenceLink,
    EvidenceSummary,
    IngestRequest,
    IngestResponse,
)
from apps.evidence_aggregator.repository import (
    count_verdicts,
    create_evidence_link,
    create_verdict,
    ensure_engagement,
    get_evidence_link,
    get_evidence_links,
    get_evidence_summary,
    get_verdict,
    list_engagements,
    list_verdicts,
)
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.ocsf import verdict_data
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)

app = FastAPI(
    title="Evidence Aggregator Service",
    description="Collects, validates, and deduplicates evidence chains.",
    version="0.1.0",
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session per request."""
    async with _session_factory() as session:
        yield session


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check for evidence-aggregator."""
    db_ok = await check_db(_engine)
    return {
        "service": "evidence-aggregator",
        "port": _settings.port_evidence_aggregator,
        "db": db_ok,
        "redis": True,
    }


@app.post(
    "/api/v1/ingest-ocsf",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_ocsf(
    payload: IngestRequest,
    session: AsyncSession = Depends(get_session),
) -> IngestResponse:
    """Convert OCSF events into Module 2 verdicts for an engagement."""
    await ensure_engagement(
        session,
        payload.engagement_id,
        payload.name,
        payload.organization,
        payload.frameworks,
    )

    existing = {
        v["verdict_id"] for v in await list_verdicts(session, payload.engagement_id)
    }
    verdict_ids: list[str] = []
    for index, event in enumerate(payload.events):
        verdict_id = f"{payload.engagement_id}-vrd-{index:04d}"
        if verdict_id in existing:
            continue
        verdict = verdict_data(event, verdict_id, payload.engagement_id)
        await create_verdict(session, verdict)
        verdict_ids.append(verdict_id)

    return IngestResponse(
        engagement_id=payload.engagement_id,
        ingested=len(verdict_ids),
        verdict_ids=verdict_ids,
    )


@app.post("/api/v1/evidence-links", response_model=EvidenceLink, status_code=201)
async def create_link(
    link: EvidenceLink,
    session: AsyncSession = Depends(get_session),
) -> EvidenceLink:
    """Persist one evidence link."""
    existing = await get_evidence_link(session, link.link_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Link '{link.link_id}' already exists",
        )
    return await create_evidence_link(session, link)


@app.get("/api/v1/engagements")
async def engagements_list(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    """Return all known engagements for dashboard selection."""
    return await list_engagements(session)


@app.get("/api/v1/evidence-links", response_model=list[EvidenceLink])
async def list_links(
    verdict_id: str | None = Query(default=None),
    control_id: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[EvidenceLink]:
    """Return stored evidence links, optionally filtered."""
    return await get_evidence_links(
        session, verdict_id=verdict_id, control_id=control_id
    )


@app.get(
    "/api/v1/evidence-summary/{engagement_id}",
    response_model=EvidenceSummary,
)
async def evidence_summary(
    engagement_id: str,
    expected: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> EvidenceSummary:
    """Return evidence totals, unique hashes, and completeness."""
    total_links, unique_hashes = await get_evidence_summary(session, engagement_id)
    if expected == 0:
        expected = await count_verdicts(session, engagement_id)
    return EvidenceSummary(
        engagement_id=engagement_id,
        total_links=total_links,
        unique_hashes=unique_hashes,
        completeness_pct=completeness_pct(unique_hashes, expected),
    )


@app.get("/api/v1/verdicts/{verdict_id}")
async def verdict_detail(
    verdict_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Return a single verdict by id."""
    verdict = await get_verdict(session, verdict_id)
    if verdict is None:
        raise HTTPException(status_code=404, detail=f"Verdict '{verdict_id}' not found")
    return verdict


@app.get("/api/v1/verdicts/{engagement_id}/engagement")
async def verdicts_for_engagement(
    engagement_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    """Return all verdicts recorded for an engagement."""
    return await list_verdicts(session, engagement_id)
