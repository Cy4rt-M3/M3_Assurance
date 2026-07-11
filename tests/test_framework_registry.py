"""Tests for framework_registry service."""

import json
from pathlib import Path
from typing import Any

import pytest

from apps.framework_registry.loader import (
    _to_control,  # type: ignore[reportPrivateUsage]
    load_all_frameworks,
    load_framework_file,
)
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


# --- loader.py ---


def test_to_control_full_fields():
    raw = {
        "control_id": "TEST-01",
        "category": "Test Category",
        "name": "Test Name",
        "description": "Test description",
        "attack_mapping": ["T1001"],
    }
    ctrl = _to_control(raw, "test_fw")
    assert ctrl.category == "Test Category"
    assert ctrl.name == "Test Name"
    assert ctrl.description == "Test description"
    assert ctrl.attack_mapping == ["T1001"]


def test_to_control_minimal_fields():
    raw = {"control_id": "TEST-02"}
    ctrl = _to_control(raw, "test_fw")
    assert ctrl.category == ""
    assert ctrl.name == "TEST-02"
    assert ctrl.description == ""
    assert ctrl.attack_mapping == []


def test_to_control_category_id_fallback():
    raw = {"control_id": "TEST-03", "category_id": "CAT-ID"}
    ctrl = _to_control(raw, "test_fw")
    assert ctrl.category == "CAT-ID"


def test_load_framework_file(tmp_path: Path) -> None:
    data = {
        "framework_id": "test_fw",
        "name": "Test Framework",
        "version": "1.0",
        "description": "A test framework",
        "regions": ["Global"],
        "controls": [
            {"control_id": "TEST-01", "category": "Cat", "description": "Desc"}
        ],
    }
    fpath: Path = tmp_path / "test_fw.json"
    fpath.write_text(json.dumps(data))
    framework, controls = load_framework_file(fpath)
    assert framework.framework_id == "test_fw"
    assert len(controls) == 1


def test_load_framework_file_defaults(tmp_path: Path) -> None:
    data = {
        "framework_id": "test_fw2",
        "name": "Test Framework 2",
        "version": "1.0",
    }
    fpath: Path = tmp_path / "test_fw2.json"
    fpath.write_text(json.dumps(data))
    framework, controls = load_framework_file(fpath)
    assert framework.description == ""
    assert framework.regions == []
    assert controls == []


def test_load_all_frameworks(tmp_path: Path) -> None:
    data: dict[str, Any] = {
        "framework_id": "abc",
        "name": "ABC",
        "version": "1.0",
        "description": "",
        "regions": [],
        "controls": [],
    }
    (tmp_path / "abc.json").write_text(json.dumps(data))
    results = load_all_frameworks(tmp_path)
    assert "abc" in results


# --- main.py endpoints ---


@pytest.mark.asyncio
async def test_list_frameworks_returns_nist_csf():
    async with make_client(app) as client:
        resp = await client.get("/frameworks")
    assert resp.status_code == 200
    ids = [f["framework_id"] for f in resp.json()]
    assert "nist_csf_2_0" in ids


@pytest.mark.asyncio
async def test_get_framework_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/nist_csf_2_0")
    assert resp.status_code == 200
    assert resp.json()["framework_id"] == "nist_csf_2_0"


@pytest.mark.asyncio
async def test_get_framework_not_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/does_not_exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_framework_controls_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/nist_csf_2_0/controls")
    assert resp.status_code == 200
    assert len(resp.json()) == 106


@pytest.mark.asyncio
async def test_get_framework_controls_not_found():
    async with make_client(app) as client:
        resp = await client.get("/frameworks/does_not_exist/controls")
    assert resp.status_code == 404
