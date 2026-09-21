"""Tests for report_publisher service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.report_publisher import channels
from apps.report_publisher.channels import download, email, webhook
from apps.report_publisher.main import app
from apps.report_publisher.models import DeliveryRequest, DeliveryStatus
from apps.report_publisher.repository import create_delivery, list_deliveries
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
    assert resp.json()["service"] == "report-publisher"


def test_delivery_request_email():
    req = DeliveryRequest(
        report_id="rpt-001",
        channel="email",
        recipient="audit@example.com",
    )
    assert req.channel == "email"


def test_delivery_request_webhook():
    req = DeliveryRequest(
        report_id="rpt-001",
        channel="webhook",
        recipient="https://hooks.example.com/notify",
    )
    assert req.channel == "webhook"


def test_delivery_status_model():
    status = DeliveryStatus(
        delivery_id="dlv-001",
        report_id="rpt-001",
        channel="email",
        recipient="audit@example.com",
        status="delivered",
    )
    assert status.status == "delivered"


def test_channels_is_supported():
    assert channels.is_supported("download") is True
    assert channels.is_supported("email") is True
    assert channels.is_supported("webhook") is True
    assert channels.is_supported("fax") is False
    assert channels.is_supported("") is False


def test_channels_dispatch():
    assert channels.dispatch("download", "ops@example.com") is True
    assert channels.dispatch("unknown", "x") is False


def test_channel_providers_validation():
    assert download.notify("someone") is True
    assert download.notify("   ") is False
    assert email.notify("audit@example.com") is True
    assert email.notify("not-an-email") is False
    assert webhook.notify("https://hooks.example.com/a") is True
    assert webhook.notify("http://insecure.example.com") is False


@pytest.mark.asyncio
async def test_delivery_repository(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    status = DeliveryStatus(
        delivery_id="dlv-repo-001",
        report_id="rpt-repo-001",
        channel="email",
        recipient="a@example.com",
        status="delivered",
    )
    async with db_session_factory() as session:
        saved = await create_delivery(session, status)
        listed = await list_deliveries(session, "rpt-repo-001")
        none = await list_deliveries(session, "rpt-missing")
    assert saved.delivery_id == "dlv-repo-001"
    assert len(listed) == 1
    assert none == []


async def _seed_report(
    db_session_factory: async_sessionmaker[AsyncSession], report_id: str
) -> None:
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO reports "
                "(report_id, engagement_id, framework_ids, score, format, content_hash)"
                " VALUES (:r, 'eng-alpha-001', ARRAY['nist_csf_2.0'], 60.0, 'html', :h)"
            ),
            {"r": report_id, "h": "b" * 64},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_publish_delivered(db_session_factory: async_sessionmaker[AsyncSession]):
    await _seed_report(db_session_factory, "rpt-pub-001")
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/publish",
            json={
                "report_id": "rpt-pub-001",
                "channel": "download",
                "recipient": "ops@example.com",
            },
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["status"] == "delivered"
        assert body["delivery_id"] == "rpt-pub-001-del-001"

        history = await client.get("/api/v1/deliveries/rpt-pub-001")
        assert any(d["delivery_id"] == "rpt-pub-001-del-001" for d in history.json())


@pytest.mark.asyncio
async def test_publish_failed_provider(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    await _seed_report(db_session_factory, "rpt-pub-002")
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/publish",
            json={
                "report_id": "rpt-pub-002",
                "channel": "webhook",
                "recipient": "http://insecure.example.com",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"


@pytest.mark.asyncio
async def test_publish_report_not_found():
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/publish",
            json={
                "report_id": "rpt-nope",
                "channel": "email",
                "recipient": "a@example.com",
            },
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_publish_unsupported_channel(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    await _seed_report(db_session_factory, "rpt-pub-003")
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/publish",
            json={
                "report_id": "rpt-pub-003",
                "channel": "fax",
                "recipient": "a@example.com",
            },
        )
    assert resp.status_code == 422
