"""Framework Registry Service — FastAPI application entry point."""

from fastapi import FastAPI, HTTPException

from apps.framework_registry import loader
from apps.framework_registry.models import Control, CrossWalk, Framework
from apps.shared.cache import build_redis, check_redis
from apps.shared.db import build_engine, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_redis = build_redis(_settings.redis_url)

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


@app.get("/frameworks")
async def list_frameworks() -> list[Framework]:
    """Return all frameworks in the registry."""
    return list(loader.load_frameworks())


@app.get("/frameworks/{framework_id}/controls")
async def list_controls(framework_id: str) -> list[Control]:
    """Return all controls for a given framework id."""
    framework = loader.get_framework(framework_id)
    if framework is None:
        raise HTTPException(
            status_code=404, detail=f"Framework '{framework_id}' not found"
        )
    return list(loader.get_controls_for_framework(framework_id))


@app.get("/controls/{control_id}/crosswalks")
async def list_crosswalks(control_id: str) -> list[CrossWalk]:
    """Return all crosswalk mappings originating from a given control id."""
    return list(loader.get_crosswalks_for_control(control_id))
