"""Tests for evidence_aggregator service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.evidence_aggregator.chain_validator import completeness_pct, is_valid_sha256
from apps.evidence_aggregator.main import app
from apps.evidence_aggregator.models import EvidenceLink, EvidenceSummary
from apps.evidence_aggregator.repository import list_engagements
from tests.conftest import make_client

_VALID_HASH = "a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8"


@pytest.mark.asyncio
async def test_health_returns_200():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_service_name():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.json()["service"] == "evidence-aggregator"


def test_is_valid_sha256_valid():
    assert is_valid_sha256(_VALID_HASH) is True


def test_is_valid_sha256_wrong_length():
    assert is_valid_sha256("abc123") is False


def test_is_valid_sha256_invalid_chars():
    assert is_valid_sha256("z" * 64) is False


def test_completeness_pct_full():
    assert completeness_pct(10, 10) == 100.0


def test_completeness_pct_partial():
    assert completeness_pct(7, 10) == 70.0


def test_completeness_pct_zero_expected():
    assert completeness_pct(0, 0) == 0.0


def test_evidence_link_model():
    link = EvidenceLink(
        link_id="lnk-001",
        control_id="DE.AE-02",
        verdict_id="vrd-001",
        evidence_hash=_VALID_HASH,
        chain_position=0,
    )
    assert link.chain_position == 0


def test_evidence_summary_model():
    summary = EvidenceSummary(
        engagement_id="eng-alpha-001",
        total_links=5,
        unique_hashes=4,
        completeness_pct=80.0,
    )
    assert summary.total_links == 5


def _event(
    disposition: str = "Allowed",
    technique: str | None = None,
    severity_id: int = 1,
) -> dict[str, object]:
    event: dict[str, object] = {
        "class_uid": 4001,
        "category_uid": 4,
        "activity_id": 1,
        "severity_id": severity_id,
        "type_uid": 400101,
        "metadata": {
            "version": "1.1.0",
            "product": {"name": "PodGamma", "vendor_name": "Cybreach"},
        },
        "disposition": disposition,
        "action": disposition,
    }
    if technique is not None:
        event["attack"] = {"technique_uid": technique}
    return event


@pytest.mark.asyncio
async def test_ingest_ocsf_created():
    engagement_id = "ing-est-001"
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/ingest-ocsf",
            json={
                "engagement_id": engagement_id,
                "name": "Ingest Test",
                "organization": "CyArt",
                "frameworks": ["nist_csf_2.0"],
                "events": [_event(), _event("Missed", "T1486")],
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["ingested"] == 2
        assert body["verdict_ids"] == [
            f"{engagement_id}-vrd-0000",
            f"{engagement_id}-vrd-0001",
        ]


@pytest.mark.asyncio
async def test_ingest_ocsf_idempotent_engagement():
    engagement_id = "ing-est-002"
    payload = {
        "engagement_id": engagement_id,
        "name": "Second Ingest",
        "organization": "CyArt",
        "frameworks": [],
        "events": [_event("No Data", "T1059")],
    }
    async with make_client(app) as client:
        first = await client.post("/api/v1/ingest-ocsf", json=payload)
        second = await client.post("/api/v1/ingest-ocsf", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201


@pytest.mark.asyncio
async def test_create_and_list_evidence_links():
    link_payload = {
        "link_id": "lnk-e2e-001",
        "control_id": "DE.AE-02",
        "verdict_id": "vrd-e2e-001",
        "evidence_hash": _VALID_HASH,
        "chain_position": 0,
    }
    async with make_client(app) as client:
        created = await client.post("/api/v1/evidence-links", json=link_payload)
        assert created.status_code == 201

        dup = await client.post("/api/v1/evidence-links", json=link_payload)
        assert dup.status_code == 409

        by_control = await client.get(
            "/api/v1/evidence-links", params={"control_id": "DE.AE-02"}
        )
        assert any(item["link_id"] == "lnk-e2e-001" for item in by_control.json())

        by_verdict = await client.get(
            "/api/v1/evidence-links", params={"verdict_id": "vrd-e2e-001"}
        )
        assert len(by_verdict.json()) == 1

        all_links = await client.get("/api/v1/evidence-links")
        assert isinstance(all_links.json(), list)


@pytest.mark.asyncio
async def test_evidence_summary_counts(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "ing-smry-001"
    verdict_id = "vrd-smry-001"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'Summary', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash)"
                " VALUES (:v, :e, 'T1078', 'Detected', 1, :h)"
            ),
            {"v": verdict_id, "e": engagement_id, "h": _VALID_HASH},
        )
        await session.execute(
            text(
                "INSERT INTO control_statuses (engagement_id, control_id, status) "
                "VALUES (:e, :c, 'Met')"
            ),
            {"e": engagement_id, "c": "DE.CM-01"},
        )
        await session.execute(
            text(
                "INSERT INTO evidence_links "
                "(link_id, control_id, verdict_id, evidence_hash, chain_position) "
                "VALUES (:l, :c, :v, :h, 0)"
            ),
            {
                "l": "lnk-smry-001",
                "c": "DE.CM-01",
                "v": "vrd-smry-001",
                "h": _VALID_HASH,
            },
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.get(f"/api/v1/evidence-summary/{engagement_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_links"] == 1
        assert body["unique_hashes"] == 1
        assert body["completeness_pct"] == 100.0

        with_expected = await client.get(
            f"/api/v1/evidence-summary/{engagement_id}", params={"expected": 2}
        )
        assert with_expected.json()["completeness_pct"] == 50.0

        empty = await client.get("/api/v1/evidence-summary/ing-no-such-eng")
        assert empty.json()["total_links"] == 0


@pytest.mark.asyncio
async def test_verdict_endpoints():
    engagement_id = "ing-vrd-001"
    async with make_client(app) as client:
        await client.post(
            "/api/v1/ingest-ocsf",
            json={
                "engagement_id": engagement_id,
                "name": "Verdict Test",
                "organization": "CyArt",
                "frameworks": [],
                "events": [_event("Allowed", "T1078")],
            },
        )
        verdict_id = f"{engagement_id}-vrd-0000"
        detail = await client.get(f"/api/v1/verdicts/{verdict_id}")
        assert detail.status_code == 200
        assert detail.json()["technique_id"] == "T1078"
        assert detail.json()["outcome"] == "Detected"

        missing = await client.get("/api/v1/verdicts/does-not-exist")
        assert missing.status_code == 404

        listed = await client.get(f"/api/v1/verdicts/{engagement_id}/engagement")
        assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_list_engagements_repository(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        rows = await list_engagements(session)
    assert isinstance(rows, list)
    assert all("engagement_id" in row for row in rows)


@pytest.mark.asyncio
async def test_list_engagements_endpoint(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "eng-list-0001"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'Dashboard', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.get("/api/v1/engagements")
        assert resp.status_code == 200
        ids = [item["engagement_id"] for item in resp.json()]
        assert engagement_id in ids
