"""Control Mapping Service — FastAPI application entry point."""
"""Control Mapping Service — FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from apps.shared.cache import build_redis, check_redis
from apps.shared.db import (
    build_engine,
    build_session_factory,
    check_db,
)
from apps.shared.settings import Settings

_settings = Settings()

_engine = build_engine(_settings.database_url)
_session_factory = build_session_factory(_engine)

_redis = build_redis(_settings.redis_url)

app = FastAPI(
    title="Control Mapping Service",
    description="Maps controls across regulatory frameworks.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/mappings/{control_id:path}")
async def get_mappings(control_id: str) -> list[dict[str, str]]:
    """
    Return all cross-framework mappings for a source control.
    """

    async with _session_factory() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    source_control_id,
                    target_control_id,
                    equivalence_level
                FROM cross_walks
                WHERE source_control_id = :control_id
                ORDER BY target_control_id;
                """
            ),
            {
                "control_id": control_id,
            },
        )

        rows = result.mappings().all()

    # if not rows:
    #     raise HTTPException(
    #         status_code=404,
    #         detail=f"No mappings found for control: {control_id}",
    #     )

    return [
        {
            "source_control_id": row.source_control_id,
            "target_control_id": row.target_control_id,
            "equivalence_level": row.equivalence_level,
        }
        for row in rows
    ]
# @app.get("/health")
# async def health() -> dict[str, object]:
#     """Liveness + dependency check for control-mapping."""

#     db_ok = await check_db(_engine)
#     redis_ok = await check_redis(_redis)

#     return {
#         "service": "control-mapping",
#         "port": _settings.port_control_mapping,
#         "db": db_ok,
#         "redis": redis_ok,
#     }


# @app.get("/mappings/{control_id:path}")
# async def get_mappings(control_id: str) -> dict[str, object]:
#     """
#     Return all cross-framework mappings for a source control.
#     """

#     async with _session_factory() as session:

#         result = await session.execute(
#             text(
#                 """
#                 SELECT
#                     source_control_id,
#                     target_control_id,
#                     equivalence_level
#                 FROM cross_walks
#                 WHERE source_control_id = :control_id
#                 ORDER BY target_control_id;
#                 """
#             ),
#             {
#                 "control_id": control_id,
#             },
#         )

#         rows = result.mappings().all()

#     if not rows:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No mappings found for control: {control_id}",
#         )
#     return [
#     {
#         "source_control_id": row.source_control_id,
#         "target_control_id": row.target_control_id,
#         "equivalence_level": row.equivalence_level,
#     }
#     for row in rows
# ]

    # return {
    #     "source_control_id": control_id,
    #     "mappings": [
    #         {
    #             "target_control_id": row.target_control_id,
    #             "equivalence_level": row.equivalence_level,
    #         }
    #         for row in rows
    #     ],
    # }


@app.get("/mappings")
async def get_all_mappings() -> dict[str, object]:
    """
    Return all crosswalk mappings.
    """

    async with _session_factory() as session:

        result = await session.execute(
            text(
                """
                SELECT
                    source_control_id,
                    target_control_id,
                    equivalence_level
                FROM cross_walks
                ORDER BY source_control_id, target_control_id;
                """
            )
        )

        rows = result.mappings().all()

    return {
        "count": len(rows),
        "mappings": [
            {
                "source_control_id": row.source_control_id,
                "target_control_id": row.target_control_id,
                "equivalence_level": row.equivalence_level,
            }
            for row in rows
        ],
    }
# from fastapi import FastAPI

# from apps.shared.cache import build_redis, check_redis
# from apps.shared.db import build_engine, check_db
# from apps.shared.settings import Settings

# _settings = Settings()
# _engine = build_engine(_settings.database_url)
# _redis = build_redis(_settings.redis_url)

# app = FastAPI(
#     title="Control Mapping Service",
#     description="Maps ATT&CK techniques and Module 2 verdicts to regulatory controls.",
#     version="0.1.0",
# )


# @app.get("/health")
# async def health() -> dict[str, object]:
#     """Liveness + dependency check for control-mapping."""
#     db_ok = await check_db(_engine)
#     redis_ok = await check_redis(_redis)
#     return {
#         "service": "control-mapping",
#         "port": _settings.port_control_mapping,
#         "db": db_ok,
#         "redis": redis_ok,
#     }
