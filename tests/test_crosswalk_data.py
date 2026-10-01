"""Cross-walk API returns the data loaded from crosswalks.json (#3)."""

import pytest

from apps.framework_registry import loader
from apps.framework_registry.main import app
from tests.conftest import make_client


def test_crosswalks_json_is_loaded() -> None:
    assert len(loader.load_crosswalks()) > 0


@pytest.mark.asyncio
async def test_crosswalk_endpoint_returns_data_for_known_control() -> None:
    async with make_client(app) as client:
        response = await client.get("/controls/GV.OC-03/crosswalks")
    body = response.json()
    assert response.status_code == 200
    assert len(body) == 2
    assert all(item["source_control_id"] == "GV.OC-03" for item in body)


@pytest.mark.asyncio
async def test_crosswalk_endpoint_returns_empty_for_unknown_control() -> None:
    async with make_client(app) as client:
        response = await client.get("/controls/NOPE-99/crosswalks")
    assert response.status_code == 200
    assert response.json() == []
