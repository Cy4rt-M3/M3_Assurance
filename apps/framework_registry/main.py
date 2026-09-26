"""Framework Registry Service — FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# from apps.framework_registry.models import Control, Framework
from apps.framework_registry.models import Control, CrossWalk, Framework
from apps.shared.cache import build_redis, check_redis
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings

_settings = Settings()
_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)
_redis = build_redis(_settings.redis_url)

app = FastAPI(
    title="Framework Registry Service",
    description="Framework catalogs and cross-walk mappings.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Return all frameworks stored in PostgreSQL."""

    async with _session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    framework_id,
                    name,
                    version,
                    description,
                    regions
                FROM frameworks
                ORDER BY framework_id
                """
            )
        )
        rows = result.mappings().all()

    return [
        Framework(
            framework_id=row["framework_id"],
            name=row["name"],
            version=row["version"],
            description=row["description"] or "",
            regions=row["regions"],
        )
        for row in rows
    ]


@app.get("/frameworks/{framework_id}", response_model=Framework)
async def get_framework(framework_id: str) -> Framework:
    """Return one framework from PostgreSQL."""

    async with _session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    framework_id,
                    name,
                    version,
                    description,
                    regions
                FROM frameworks
                WHERE framework_id = :framework_id
                """
            ),
            {"framework_id": framework_id},
        )

        row = result.mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Framework not found",
        )

    return Framework(
        framework_id=row["framework_id"],
        name=row["name"],
        version=row["version"],
        description=row["description"] or "",
        regions=row["regions"],
    )


@app.get(
    "/frameworks/{framework_id}/controls",
    response_model=list[Control],
)
async def get_framework_controls(framework_id: str) -> list[Control]:
    """Return all controls belonging to a framework."""

    async with _session_factory() as session:
        framework_result = await session.execute(
            text(
                """
                SELECT framework_id
                FROM frameworks
                WHERE framework_id = :framework_id
                """
            ),
            {"framework_id": framework_id},
        )

        if framework_result.first() is None:
            raise HTTPException(
                status_code=404,
                detail="Framework not found",
            )

        result = await session.execute(
            text(
                """
                SELECT
                    control_id,
                    framework_id,
                    category,
                    name,
                    description,
                    attack_mapping
                FROM controls
                WHERE framework_id = :framework_id
                ORDER BY control_id
                """
            ),
            {"framework_id": framework_id},
        )

        rows = result.mappings().all()

    return [
        Control(
            control_id=row["control_id"],
            framework_id=row["framework_id"],
            category=row["category"],
            name=row["name"],
            description=row["description"] or "",
            attack_mapping=row["attack_mapping"],
        )
        for row in rows
    ]
@app.get(
    "/controls/{control_id}/mappings",
    response_model=list[CrossWalk],
)
async def get_control_mappings(control_id: str) -> list[CrossWalk]:
    """Return cross-framework mappings for a control."""

    async with _session_factory() as session:
        control_result = await session.execute(
            text(
                """
                SELECT control_id
                FROM controls
                WHERE control_id = :control_id
                """
            ),
            {"control_id": control_id},
        )

        if control_result.first() is None:
            raise HTTPException(
                status_code=404,
                detail="Control not found",
            )

        result = await session.execute(
            text(
                """
                SELECT
                    source_control_id,
                    target_control_id,
                    equivalence_level
                FROM cross_walks
                WHERE source_control_id = :control_id
                ORDER BY target_control_id
                """
            ),
            {"control_id": control_id},
        )

        rows = result.mappings().all()

    return [
        CrossWalk(
            source_control_id=row["source_control_id"],
            target_control_id=row["target_control_id"],
            equivalence_level=row["equivalence_level"],
        )
        for row in rows
    ]




# from fastapi import FastAPI

# from apps.shared.cache import build_redis, check_redis
# from apps.shared.db import build_engine, check_db
# from apps.shared.settings import Settings

# _settings = Settings()
# _engine = build_engine(_settings.database_url)
# _redis = build_redis(_settings.redis_url)

# app = FastAPI(
#     title="Framework Registry Service",
#     description="Framework catalogs and cross-walk mappings.",
#     version="0.1.0",
# )


# @app.get("/health")
# async def health() -> dict[str, object]:
#     """Liveness + dependency check for framework-registry."""
#     db_ok = await check_db(_engine)
    # redis_ok = await check_redis(_redis)
    # return {
    #     "service": "framework-registry",
    #     "port": _settings.port_framework_registry,
    #     "db": db_ok,
    #     "redis": redis_ok,
    # }
