"""Evidence Aggregator FastAPI service."""

from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.evidence_aggregator.models import EvidenceLink, EvidenceSummary
from apps.evidence_aggregator.repository import (
    create_evidence_link,
    get_evidence_links,
    get_evidence_summary,
)
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings


settings = Settings()

engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)


app = FastAPI(
    title="Evidence Aggregator Service",
    description="Collects, validates, and deduplicates evidence chains.",
    version="0.1.0",
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one database session per request."""
    async with session_factory() as session:
        yield session


@app.get(
    "/health",
    summary="Health",
)
async def health() -> dict[str, object]:
    """Return service health and database connectivity."""
    db_ok = await check_db(engine)

    return {
        "service": "evidence-aggregator",
        "port": settings.port_evidence_aggregator,
        "db": db_ok,
        "redis": True,
    }


@app.post(
    "/evidence-links",
    response_model=EvidenceLink,
    status_code=status.HTTP_201_CREATED,
    summary="Add Evidence Link",
    responses={
        201: {
            "description": "Evidence link created successfully.",
        },
        409: {
            "description": "Evidence link could not be stored.",
        },
        422: {
            "description": "Invalid request payload.",
        },
    },
)
async def create_link(
    link: EvidenceLink,
    session: AsyncSession = Depends(get_session),
) -> EvidenceLink:
    """Persist one evidence link."""
    try:
        return await create_evidence_link(session, link)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@app.get(
    "/evidence-links",
    response_model=list[EvidenceLink],
    summary="List Evidence Links",
    responses={
        200: {
            "description": "Stored evidence links.",
        },
        422: {
            "description": "Invalid query parameters.",
        },
    },
)
async def list_links(
    verdict_id: str | None = Query(
        default=None,
        description="Filter evidence links by verdict ID.",
    ),
    control_id: str | None = Query(
        default=None,
        description="Filter evidence links by control ID.",
    ),
    session: AsyncSession = Depends(get_session),
) -> list[EvidenceLink]:
    """Return stored evidence links, optionally filtered."""
    return await get_evidence_links(
        session,
        verdict_id=verdict_id,
        control_id=control_id,
    )


@app.get(
    "/evidence-summary/{engagement_id}",
    response_model=EvidenceSummary,
    summary="Evidence Summary",
    responses={
        200: {
            "description": "Evidence aggregation summary.",
        },
        422: {
            "description": "Invalid path or query parameters.",
        },
    },
)
async def evidence_summary(
    engagement_id: str,
    expected: int = Query(
        default=0,
        ge=0,
        description=(
            "Expected number of evidence links used for completeness calculation."
        ),
    ),
    session: AsyncSession = Depends(get_session),
) -> EvidenceSummary:
    """Return evidence totals, unique hashes, and completeness."""
    total_links, unique_hashes = await get_evidence_summary(
        session,
        engagement_id,
    )

    completeness = round(total_links / expected * 100, 1) if expected > 0 else 0.0

    return EvidenceSummary(
        engagement_id=engagement_id,
        total_links=total_links,
        unique_hashes=unique_hashes,
        completeness_pct=completeness,
    )
