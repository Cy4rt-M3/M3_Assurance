"""Framework Registry Service — FastAPI application entry point."""

from fastapi import FastAPI, HTTPException

from apps.framework_registry.loader import load_all_frameworks
from apps.framework_registry.models import Control, Framework
from apps.shared.cache import build_redis, check_redis
from apps.shared.db import build_engine, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_redis = build_redis(_settings.redis_url)

# Load all framework definitions (e.g. nist_csf_2_0.json) into memory at startup
_frameworks = load_all_frameworks()

app = FastAPI(
    title="Framework Registry Service",
    description="Framework catalogs and cross-walk mappings.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, object]:
    """Liveness + dependency check for framework-registry."""
    db_ok = await check_db(_engine)
    redis_ok = await check_redis(_redis)
    return {
        "service": "framework-registry",
        "port": _settings.port_framework_registry,
        "db": db_ok,
        "redis": redis_ok,
    }


@app.get("/frameworks", response_model=list[Framework])
async def list_frameworks() -> list[Framework]:
    return [fw for fw, _ in _frameworks.values()]


@app.get("/frameworks/{framework_id}", response_model=Framework)
async def get_framework(framework_id: str) -> Framework:
    if framework_id not in _frameworks:
        raise HTTPException(status_code=404, detail="Framework not found")
    fw, _ = _frameworks[framework_id]
    return fw


@app.get("/frameworks/{framework_id}/controls", response_model=list[Control])
async def get_framework_controls(framework_id: str) -> list[Control]:
    if framework_id not in _frameworks:
        raise HTTPException(status_code=404, detail="Framework not found")
    _, controls = _frameworks[framework_id]
    return controls
