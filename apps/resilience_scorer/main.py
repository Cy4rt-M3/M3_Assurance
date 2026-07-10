"""Resilience Scorer Service — FastAPI application entry point."""

from fastapi import FastAPI

from apps.resilience_scorer.blast_radius import calculate_blast_radius
from apps.resilience_scorer.calculator import (
    score_band,
    weighted_risk_score,
)
from apps.resilience_scorer.models import (
    BlastRadiusRequest,
    BlastRadiusResponse,
    ThreatIntelRequest,
    ThreatIntelResponse,
    WeightedRiskResponse,
)
from apps.resilience_scorer.threat_intel import (
    fetch_cvss,
    fetch_epss,
)
from apps.shared.cache import build_redis, check_redis
from apps.shared.db import build_engine, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_redis = build_redis(_settings.redis_url)

app = FastAPI(
    title="Resilience Scorer Service",
    description="Computes composite Resilience Score.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check."""
    db_ok = await check_db(_engine)
    redis_ok = await check_redis(_redis)

    return {
        "service": "resilience-scorer",
        "port": _settings.port_resilience_scorer,
        "db": db_ok,
        "redis": redis_ok,
    }


@app.post("/threat-intel", response_model=ThreatIntelResponse)
async def threat_intel(
    request: ThreatIntelRequest,
) -> ThreatIntelResponse:
    """Fetch CVSS and EPSS values."""

    cvss = await fetch_cvss(request.cve_id)
    epss = await fetch_epss(request.cve_id)

    return ThreatIntelResponse(
        cve_id=request.cve_id,
        cvss_score=cvss,
        epss_score=epss,
    )


@app.post("/blast-radius", response_model=BlastRadiusResponse)
async def blast_radius(
    request: BlastRadiusRequest,
) -> BlastRadiusResponse:
    """Calculate blast radius."""

    score = calculate_blast_radius(
        exposure="external" if request.internet_facing else "internal",
        criticality=("high" if request.production else "medium"),
        internet_facing=request.internet_facing,
    )

    return BlastRadiusResponse(
        asset_id=request.asset_id,
        blast_radius_score=score,
    )


@app.post("/weighted-risk", response_model=WeightedRiskResponse)
async def weighted_risk(
    request: ThreatIntelRequest,
) -> WeightedRiskResponse:
    """Calculate overall weighted risk."""

    cvss = await fetch_cvss(request.cve_id)
    epss = await fetch_epss(request.cve_id)

    blast = calculate_blast_radius(
        exposure="external",
        criticality="high",
        internet_facing=True,
    )

    score = weighted_risk_score(
        cvss=cvss,
        epss=epss,
        blast_radius=blast,
    )

    return WeightedRiskResponse(
        cvss_score=cvss,
        epss_score=epss,
        blast_radius_score=blast,
        final_score=score,
        band=score_band(score),
    )
