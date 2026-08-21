"""Tests for framework_registry service."""

import pytest

from apps.framework_registry import loader
from apps.framework_registry.main import app
from apps.framework_registry.models import Control, CrossWalk, Framework
from tests.conftest import make_client


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


# ─── loader.py ────────────────────────────────────────────────


def test_load_frameworks_returns_all():
    frameworks = loader.load_frameworks()
    assert len(frameworks) == 8
    assert all(isinstance(fw, Framework) for fw in frameworks)


def test_load_controls_returns_all():
    controls = loader.load_controls()
    assert len(controls) == 491
    assert all(isinstance(c, Control) for c in controls)


def test_load_crosswalks_returns_all():
    crosswalks = loader.load_crosswalks()
    assert len(crosswalks) > 0
    assert all(isinstance(cw, CrossWalk) for cw in crosswalks)


def test_get_framework_found():
    fw = loader.get_framework("nist_csf_2_0_2")
    assert fw is not None
    assert fw.name == "NIST CSF 2.0"


def test_get_framework_not_found():
    fw = loader.get_framework("does-not-exist")
    assert fw is None


def test_get_controls_for_framework():
    controls = loader.get_controls_for_framework("gdpr_regulation_eu_2016_679")
    assert len(controls) == 7
    assert all(c.framework_id == "gdpr_regulation_eu_2016_679" for c in controls)


def test_get_controls_for_unknown_framework():
    controls = loader.get_controls_for_framework("does-not-exist")
    assert controls == ()


def test_get_crosswalks_for_control_found():
    crosswalks = loader.get_crosswalks_for_control("GV.OC-03")
    assert len(crosswalks) == 2
    assert all(cw.source_control_id == "GV.OC-03" for cw in crosswalks)


def test_get_crosswalks_for_control_not_found():
    crosswalks = loader.get_crosswalks_for_control("does-not-exist")
    assert crosswalks == ()


# ─── endpoints ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_frameworks_endpoint():
    async with make_client(app) as client:
        resp = await client.get("/frameworks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8
    assert {fw["framework_id"] for fw in data} >= {"gdpr_regulation_eu_2016_679"}


@pytest.mark.asyncio
async def test_list_controls_endpoint_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/nis2_directive_eu_2022_2555/controls")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 7


@pytest.mark.asyncio
async def test_list_controls_endpoint_framework_not_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/does-not-exist/controls")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_crosswalks_endpoint_found():
    async with make_client(app) as client:
        resp = await client.get("/controls/GV.OC-03/crosswalks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_crosswalks_endpoint_empty():
    async with make_client(app) as client:
        resp = await client.get("/controls/does-not-exist/crosswalks")
    assert resp.status_code == 200
    assert resp.json() == []
