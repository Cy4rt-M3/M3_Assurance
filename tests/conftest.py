"""pytest conftest — session-scoped real Postgres + Redis fixtures. No mocks."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from apps.shared.cache import build_redis
from apps.shared.db import build_engine, build_session_factory
from apps.shared.settings import Settings

_FIXTURES = Path(__file__).parent / "fixtures"

_settings = Settings()
_TEST_DB_URL = _settings.database_test_url
_REDIS_URL = _settings.redis_url


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return _TEST_DB_URL


@pytest.fixture(scope="session")
def redis_url() -> str:
    return _REDIS_URL


@pytest_asyncio.fixture(scope="session")
async def db_engine(test_db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    engine = build_engine(test_db_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return build_session_factory(db_engine)


@pytest_asyncio.fixture(scope="session")
async def redis_client(redis_url: str) -> AsyncGenerator[Redis, None]:
    client = build_redis(redis_url)
    yield client
    await client.aclose()


_TABLE_NAMES = (
    "engagements",
    "verdicts",
    "evidence_links",
    "control_statuses",
    "frameworks",
    "controls",
    "cross_walks",
    "resilience_scores",
    "gap_analyses",
    "reports",
    "deliveries",
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_db(db_engine: AsyncEngine) -> None:
    """Reset the test DB, then load fixture JSON files once per session."""
    async with db_engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE {', '.join(_TABLE_NAMES)} RESTART IDENTITY CASCADE")
        )
    await load_fixture_registry(db_engine)


async def load_fixture_registry(db_engine: AsyncEngine) -> None:
    """Insert the fixture frameworks/controls into the test DB."""
    async with db_engine.begin() as conn:
        for framework in _load("frameworks.json"):
            await conn.execute(
                text(
                    "INSERT INTO frameworks "
                    "(framework_id, name, version, description, regions)"
                    " VALUES (:fid, :name, :ver, :desc, :regions)"
                    " ON CONFLICT (framework_id) DO NOTHING"
                ),
                {
                    "fid": framework["framework_id"],
                    "name": framework["name"],
                    "ver": framework["version"],
                    "desc": framework["description"],
                    "regions": framework["regions"],
                },
            )
        for ctrl in _load("controls.json"):
            await conn.execute(
                text(
                    "INSERT INTO controls "
                    "(control_id, framework_id, category, name, "
                    "description, attack_mapping)"
                    " VALUES (:cid, :fid, :cat, :name, :desc, :atk)"
                    " ON CONFLICT (control_id) DO NOTHING"
                ),
                {
                    "cid": ctrl["control_id"],
                    "fid": ctrl["framework_id"],
                    "cat": ctrl["category"],
                    "name": ctrl["name"],
                    "desc": ctrl["description"],
                    "atk": ctrl["attack_mapping"],
                },
            )


def _load(filename: str) -> list[dict[str, Any]]:
    return json.loads((_FIXTURES / filename).read_text())  # type: ignore[no-any-return]


def make_client(app: FastAPI) -> AsyncClient:
    """Create a test ASGI client for a FastAPI app (no running server needed)."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def service_apps_on_test_db(
    db_engine: AsyncEngine,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[None, None]:
    """Point every service app at the test database for the whole session."""
    from apps.control_mapping import main as control_mapping_main
    from apps.evidence_aggregator import main as evidence_aggregator_main
    from apps.gap_analyzer import main as gap_analyzer_main
    from apps.pipeline import engine as pipeline_engine
    from apps.report_generator import main as report_generator_main
    from apps.report_publisher import main as report_publisher_main
    from apps.resilience_scorer import main as resilience_scorer_main

    for module in (
        control_mapping_main,
        evidence_aggregator_main,
        gap_analyzer_main,
        report_generator_main,
        report_publisher_main,
        resilience_scorer_main,
        pipeline_engine,
    ):
        setattr(module, "_engine", db_engine)  # noqa: B010
        setattr(module, "_session_factory", db_session_factory)  # noqa: B010
    yield
