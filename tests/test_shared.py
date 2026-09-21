"""Tests for apps/shared — settings, db, cache."""

import pytest

from apps.shared.cache import build_redis, check_redis
from apps.shared.db import build_engine, build_session_factory, check_db
from apps.shared.settings import Settings


def test_settings_defaults():
    s = Settings()
    assert s.port_control_mapping == 10001
    assert s.port_report_publisher == 10007


def test_settings_ports_sequential():
    s = Settings()
    ports = [
        s.port_control_mapping,
        s.port_evidence_aggregator,
        s.port_gap_analyzer,
        s.port_resilience_scorer,
        s.port_report_generator,
        s.port_framework_registry,
        s.port_report_publisher,
    ]
    assert len(set(ports)) == 7, "Each service must have a unique port"


@pytest.mark.asyncio
async def test_db_reachable(test_db_url: str):
    engine = build_engine(test_db_url)
    assert await check_db(engine)
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_unreachable():
    engine = build_engine("postgresql+asyncpg://localhost:9999/assurance")
    assert await check_db(engine) is False
    await engine.dispose()


def test_build_session_factory(test_db_url: str):
    engine = build_engine(test_db_url)
    factory = build_session_factory(engine)
    assert factory is not None


@pytest.mark.asyncio
async def test_redis_reachable(redis_url: str):
    client = build_redis(redis_url)
    assert await check_redis(client)
    await client.aclose()


@pytest.mark.asyncio
async def test_redis_unreachable():
    client = build_redis("redis://localhost:9999/0")
    assert await check_redis(client) is False
    await client.aclose()


def test_outcome_from_disposition_all_known():
    from apps.shared.ocsf import outcome_from_disposition

    assert outcome_from_disposition("Blocked") == "Detected"
    assert outcome_from_disposition("Detected") == "Detected"
    assert outcome_from_disposition("Allowed") == "Detected"
    assert outcome_from_disposition("Missed") == "Missed"
    assert outcome_from_disposition("No Data") == "No Data"
    assert outcome_from_disposition("None") == "No Data"


def test_outcome_from_disposition_unknown():
    from apps.shared.ocsf import outcome_from_disposition

    assert outcome_from_disposition("Sideways") == "Partial"
    assert outcome_from_disposition("") == "Partial"


def test_technique_id_from_event_variants():
    from apps.shared.ocsf import DEFAULT_TECHNIQUE_ID, technique_id_from_event

    assert technique_id_from_event({"attack": {"technique_uid": "T1566"}}) == "T1566"
    assert technique_id_from_event({"attack": {}}) == DEFAULT_TECHNIQUE_ID
    assert technique_id_from_event({"technique_uid": "T1059"}) == "T1059"
    assert technique_id_from_event({"technique_id": "T1490"}) == "T1490"
    assert technique_id_from_event({"technique": "T1078"}) == "T1078"
    assert technique_id_from_event({"severity_id": 2}) == DEFAULT_TECHNIQUE_ID


def test_severity_name_all_values():
    from apps.shared.ocsf import severity_name

    assert severity_name(0) == "Unknown"
    assert severity_name(1) == "Informational"
    assert severity_name(2) == "Low"
    assert severity_name(3) == "Medium"
    assert severity_name(4) == "High"
    assert severity_name(5) == "Critical"
    assert severity_name(9) == "Unknown"


def test_severity_id_from_event_variants():
    from apps.shared.ocsf import severity_id_from_event

    assert severity_id_from_event({"severity_id": 4}) == 4
    assert severity_id_from_event({"severity_id": "3"}) == 3
    assert severity_id_from_event({"severity_id": "nope"}) == 0
    assert severity_id_from_event({}) == 0


def test_evidence_hash_deterministic():
    from apps.shared.ocsf import evidence_hash

    event = {"class_uid": 4001, "disposition": "Allowed"}
    first = evidence_hash(event)
    assert first == evidence_hash(dict(event))
    assert len(first) == 64
    assert evidence_hash({"b": 1, "a": 2}) != evidence_hash({"a": 2, "b": 3})


def test_verdict_data_builds_payload():
    from apps.shared.ocsf import verdict_data

    payload = verdict_data(
        {
            "disposition": "Missed",
            "severity_id": "4",
            "attack": {"technique_uid": "T1486"},
        },
        "eng-001-vrd-0001",
        "eng-001",
    )
    assert payload == {
        "verdict_id": "eng-001-vrd-0001",
        "engagement_id": "eng-001",
        "technique_id": "T1486",
        "outcome": "Missed",
        "severity_id": 4,
        "evidence_hash": payload["evidence_hash"],
    }


def test_attack_tactics_tactics_for_known_and_unknown():
    from apps.shared.attack_tactics import tactics_for

    assert "Initial Access" in tactics_for("T1078")
    assert tactics_for("T9999") == frozenset()


def test_attack_tactics_labels_for():
    from apps.shared.attack_tactics import labels_for

    labels = labels_for("T1078")
    assert "T1078" in labels
    assert "Valid Accounts" in labels
    assert "Persistence" in labels
    assert "T1486" in labels_for("T1486")


def test_attack_tactics_effective_mapping():
    from apps.shared.attack_tactics import effective_mapping

    tested = {"T1078", "T1486", "T1566"}
    assert effective_mapping(["T1486"], tested) == ["T1486"]
    assert effective_mapping(["Valid Accounts"], tested) == ["T1078"]
    assert effective_mapping(["Initial Access"], tested) == ["T1078", "T1566"]
    assert effective_mapping(["Exfiltration"], tested) == []
    assert effective_mapping([], tested) == []
