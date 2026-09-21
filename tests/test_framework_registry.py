"""Tests for framework_registry service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import apps.framework_registry.seed as seed_module
from apps.framework_registry import loader
from apps.framework_registry.main import app
from apps.framework_registry.models import Control, CrossWalk, Framework
from tests.conftest import load_fixture_registry, make_client


async def _restore_fixture_registry(db_engine: AsyncEngine) -> None:
    """Seed() rewrites real registry ids over fixture control rows; restore."""
    async with db_engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE frameworks, controls RESTART IDENTITY CASCADE")
        )
    await load_fixture_registry(db_engine)


@pytest.mark.asyncio
async def test_health_returns_200():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_service_name():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.json()["service"] == "framework-registry"


def test_framework_model():
    fw = Framework(
        framework_id="nist_csf_2.0",
        name="NIST CSF",
        version="2.0",
        description="Six core functions.",
        regions=["global", "us"],
    )
    assert fw.framework_id == "nist_csf_2.0"


def test_control_model():
    ctrl = Control(
        control_id="DE.AE-02",
        framework_id="nist_csf_2.0",
        category="Detect",
        name="Anomalies and Events",
        description="Detect anomalous events.",
        attack_mapping=["T1486", "T1059"],
    )
    assert len(ctrl.attack_mapping) == 2


def test_cross_walk_model():
    cw = CrossWalk(
        source_control_id="DE.AE-02",
        target_control_id="ISO-8.16",
        equivalence_level="Partial",
    )
    assert cw.equivalence_level == "Partial"


def test_loader_loads_registry_definitions():
    frameworks = loader.load_frameworks()
    controls = loader.load_controls()
    crosswalks = loader.load_crosswalks()
    assert len(frameworks) == 8
    assert len(controls) == 491
    assert len(crosswalks) > 0


def test_loader_get_framework_found_and_missing():
    assert loader.get_framework("nist_csf_2_0_2") is not None
    assert loader.get_framework("no-such-framework") is None


def test_loader_get_controls_for_framework():
    controls = loader.get_controls_for_framework("nist_csf_2_0_2")
    assert len(controls) == 99
    assert all(c.framework_id == "nist_csf_2_0_2" for c in controls)


def test_loader_get_crosswalks_for_control():
    known = loader.load_controls()[0]
    crosswalks = loader.get_crosswalks_for_control(known.control_id)
    assert isinstance(crosswalks, tuple)
    assert loader.get_crosswalks_for_control("no-such-control") == ()


@pytest.mark.asyncio
async def test_list_frameworks_endpoint():
    async with make_client(app) as client:
        resp = await client.get("/frameworks")
    body = resp.json()
    assert resp.status_code == 200
    ids = {f["framework_id"] for f in body}
    assert {"nist_csf_2_0_2", "iso_27001_2022", "pci_dss_v4_0_1"} <= ids


@pytest.mark.asyncio
async def test_list_controls_endpoint():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/nist_csf_2_0_2/controls")
    assert resp.status_code == 200
    assert len(resp.json()) == 99


@pytest.mark.asyncio
async def test_list_controls_endpoint_not_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/unknown/controls")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_crosswalks_endpoint():
    known = loader.load_controls()[0]
    async with make_client(app) as client:
        resp = await client.get(f"/controls/{known.control_id}/crosswalks")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_seed_build_session_factory_from_settings():
    factory = seed_module.build_session_factory_from_settings()
    assert factory is not None


@pytest.mark.asyncio
async def test_seed_populates_registry(
    db_session_factory: async_sessionmaker[AsyncSession], db_engine: AsyncEngine
):
    frameworks, controls = await seed_module.seed(db_session_factory)
    assert frameworks == 8
    assert controls == 491
    await _restore_fixture_registry(db_engine)


@pytest.mark.asyncio
async def test_seed_main_entrypoint(
    monkeypatch: pytest.MonkeyPatch,
    db_session_factory: async_sessionmaker[AsyncSession],
    db_engine: AsyncEngine,
):
    monkeypatch.setattr(
        seed_module,
        "build_session_factory_from_settings",
        lambda: db_session_factory,
    )
    await seed_module.main()
    await _restore_fixture_registry(db_engine)
