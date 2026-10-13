"""Tests for apps.resilience_scorer.threat_intel and its endpoint."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from apps.resilience_scorer import main as resilience_main
from apps.resilience_scorer import threat_intel

CVE = "CVE-2024-0001"


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    response: _FakeResponse

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    async def get(
        self, _url: str, params: dict[str, str] | None = None
    ) -> _FakeResponse:
        assert params is not None
        return type(self).response


def _patch_client(monkeypatch: pytest.MonkeyPatch, response: _FakeResponse) -> None:
    _FakeClient.response = response
    monkeypatch.setattr(threat_intel.httpx, "AsyncClient", _FakeClient)


def test_extract_cvss_v31() -> None:
    metrics = {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}]}
    assert threat_intel._extract_cvss(metrics) == 9.8


def test_extract_cvss_v30() -> None:
    metrics = {"cvssMetricV30": [{"cvssData": {"baseScore": 7.5}}]}
    assert threat_intel._extract_cvss(metrics) == 7.5


def test_extract_cvss_missing() -> None:
    assert threat_intel._extract_cvss({}) == 0.0


@pytest.mark.asyncio
async def test_fetch_cvss_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(500))
    assert await threat_intel.fetch_cvss(CVE) == 0.0


@pytest.mark.asyncio
async def test_fetch_cvss_no_vulnerabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(200, {"vulnerabilities": []}))
    assert await threat_intel.fetch_cvss(CVE) == 0.0


@pytest.mark.asyncio
async def test_fetch_cvss_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "vulnerabilities": [
            {"cve": {"metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}]}}}
        ]
    }
    _patch_client(monkeypatch, _FakeResponse(200, payload))
    assert await threat_intel.fetch_cvss(CVE) == 9.8


@pytest.mark.asyncio
async def test_fetch_epss_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(503))
    assert await threat_intel.fetch_epss(CVE) == 0.0


@pytest.mark.asyncio
async def test_fetch_epss_no_records(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(200, {"data": []}))
    assert await threat_intel.fetch_epss(CVE) == 0.0


@pytest.mark.asyncio
async def test_fetch_epss_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, _FakeResponse(200, {"data": [{"epss": "0.42"}]}))
    assert await threat_intel.fetch_epss(CVE) == 0.42


@pytest.mark.asyncio
async def test_threat_intel_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_cvss(_cve_id: str) -> float:
        return 9.8

    async def fake_epss(_cve_id: str) -> float:
        return 0.42

    monkeypatch.setattr(resilience_main, "fetch_cvss", fake_cvss)
    monkeypatch.setattr(resilience_main, "fetch_epss", fake_epss)

    transport = ASGITransport(app=resilience_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/threat-intel", json={"cve_id": CVE})

    assert response.status_code == 200
    body = response.json()
    assert body["cve_id"] == CVE
    assert body["cvss_score"] == 9.8
    assert body["epss_score"] == 0.42
