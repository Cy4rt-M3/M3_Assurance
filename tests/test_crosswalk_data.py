"""Cross-walk API returns the data loaded from crosswalks.json (#3)."""

from fastapi.testclient import TestClient

from apps.framework_registry import loader
from apps.framework_registry.main import app

client = TestClient(app)


def test_crosswalks_json_is_loaded() -> None:
    assert len(loader.load_crosswalks()) > 0


def test_crosswalk_endpoint_returns_data_for_known_control() -> None:
    response = client.get("/controls/GV.OC-03/crosswalks")
    body = response.json()
    assert response.status_code == 200
    assert len(body) == 2
    assert all(item["source_control_id"] == "GV.OC-03" for item in body)


def test_crosswalk_endpoint_returns_empty_for_unknown_control() -> None:
    response = client.get("/controls/NOPE-99/crosswalks")
    assert response.status_code == 200
    assert response.json() == []
