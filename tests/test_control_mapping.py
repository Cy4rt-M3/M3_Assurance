"""Tests for control_mapping service."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.control_mapping import mapper, repository
from apps.control_mapping.main import app
from apps.control_mapping.mappers import coverage_pct, outcome_to_status
from apps.control_mapping.models import (
    ControlMappingRequest,
    ControlMappingResponse,
    ControlStatus,
)
from apps.evidence_aggregator.models import EvidenceLink
from apps.framework_registry.models import Control
from tests.conftest import make_client


@pytest.mark.asyncio
async def test_health_returns_200():
    async with make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_db_and_redis_ok():
    async with make_client(app) as client:
        resp = await client.get("/health")
    body = resp.json()
    assert body["service"] == "control-mapping"
    assert body["db"] is True
    assert body["redis"] is True


def test_outcome_to_status_detected():
    assert outcome_to_status("Detected") == "Met"


def test_outcome_to_status_missed():
    assert outcome_to_status("Missed") == "Not Met"


def test_outcome_to_status_no_data():
    assert outcome_to_status("No Data") == "Not Met"


def test_outcome_to_status_partial():
    assert outcome_to_status("Partial") == "Partial"


def test_outcome_to_status_unknown_defaults_partial():
    assert outcome_to_status("SomethingElse") == "Partial"


def test_coverage_pct_all_met():
    statuses = {"c1": "Met", "c2": "Met", "c3": "Met"}
    assert coverage_pct(statuses) == 100.0


def test_coverage_pct_half_met():
    statuses = {"c1": "Met", "c2": "Not Met"}
    assert coverage_pct(statuses) == 50.0


def test_coverage_pct_empty():
    assert coverage_pct({}) == 0.0


def test_control_mapping_request_model():
    req = ControlMappingRequest(
        verdict_id="vrd-001",
        framework_ids=["nist_csf_2.0"],
        engagement_id="eng-alpha-001",
    )
    assert req.verdict_id == "vrd-001"


def test_control_status_model():
    cs = ControlStatus(control_id="DE.AE-02", status="Met", evidence_hash=None)
    assert cs.status == "Met"


def test_control_mapping_response_model():
    resp = ControlMappingResponse(
        engagement_id="eng-alpha-001",
        control_statuses={"DE.AE-02": "Met"},
        coverage_pct=100.0,
        framework_ids=["nist_csf_2.0"],
    )
    assert resp.coverage_pct == 100.0


def _control(control_id: str, mapping: list[str]) -> Control:
    return Control(
        control_id=control_id,
        framework_id="nist_csf_2.0",
        category="Detect",
        name=control_id,
        description="Test control",
        attack_mapping=mapping,
    )


def _verdict(
    verdict_id: str,
    technique_id: str,
    outcome: str,
    evidence_hash: str,
) -> dict[str, object]:
    return {
        "verdict_id": verdict_id,
        "engagement_id": "eng-alpha-001",
        "technique_id": technique_id,
        "outcome": outcome,
        "severity_id": 1,
        "evidence_hash": evidence_hash,
    }


def test_mapper_control_id_from_verdict():
    assert mapper.control_id_from_verdict("DE.AE-02", "vrd-001") == "DE.AE-02:vrd-001"


def test_mapper_evidence_for_control_matched_and_none():
    verdicts = [_verdict("v1", "T1486", "Detected", "h1")]
    control = _control("DE.AE-02", ["T1486", "T1490"])
    assert mapper.evidence_for_control(control, verdicts) == "h1"
    assert (
        mapper.evidence_for_control(_control("DE.CM-01", ["T1078"]), verdicts) is None
    )


def test_mapper_technique_statuses_groups_by_technique():
    grouped = mapper.technique_statuses(
        [
            _verdict("v1", "T1486", "Detected", "h1"),
            _verdict("v2", "T1486", "Missed", "h2"),
            _verdict("v3", "T1078", "Partial", "h3"),
        ]
    )
    assert grouped["T1486"] == {"Detected", "Missed"}
    assert grouped["T1078"] == {"Partial"}


def test_mapper_relevant_techniques():
    assert mapper.relevant_techniques(
        ["T1486", "T1490", "T1059"], {"T1486", "T1059"}
    ) == ["T1486", "T1059"]
    assert mapper.relevant_techniques(["T1566"], {"T1486"}) == []


def test_mapper_control_status_worst_case():
    grouped = {"T1486": {"Detected"}, "T1490": {"Missed"}}
    assert (
        mapper.mapped_control_status(["T1486", "T1490"], set(grouped), grouped)
        == "Not Met"
    )
    assert mapper.mapped_control_status(["T1486"], {"T1486"}, grouped) == "Met"
    assert (
        mapper.mapped_control_status(["T1078"], {"T1078"}, {"T1078": {"No Data"}})
        == "Not Met"
    )
    assert mapper.mapped_control_status(["T1486"], set(), {}) is None


def test_mapper_build_mapping_technique_and_tactic():
    verdicts = [
        _verdict("v1", "T1486", "Detected", "h1"),
        _verdict("v2", "T1078", "Missed", "h2"),
    ]
    controls = [
        _control("RS.MI-01", ["T1486", "T1490"]),
        _control("DE.CM-01", ["T1078", "T1098"]),
        _control("ISO-8.16", ["Impact"]),
        _control("ISO-8.7", ["Exfiltration"]),
    ]
    statuses, links = mapper.build_mapping(controls, verdicts)
    assert statuses["RS.MI-01"] == "Met"
    assert statuses["DE.CM-01"] == "Not Met"
    assert statuses["ISO-8.16"] == "Met"
    assert "ISO-8.7" not in statuses
    assert any(
        isinstance(link, EvidenceLink) and link.control_id == "ISO-8.16"
        for link in links
    )
    assert links[0].link_id == "RS.MI-01:v1"


def test_mapper_build_mapping_empty_controls():
    assert mapper.build_mapping([], []) == ({}, [])


def test_mapper_verdict_outcome_unknown_defaults_no_data():
    assert mapper._verdict_outcome(set()) == "No Data"  # type: ignore[reportPrivateUsage]
    assert mapper._verdict_outcome({"No Data"}) == "No Data"  # type: ignore[reportPrivateUsage]


def test_mapper_build_mapping_skips_unmapped_status(monkeypatch: pytest.MonkeyPatch):
    controls = [_control("RS.MI-01", ["T1486", "T1490"])]
    verdicts = [_verdict("v1", "T1486", "Detected", "h1")]

    def _empty_mapping(_mapping: list[str], _tested: set[str]) -> set[str]:
        return {"T9999"}

    monkeypatch.setattr(mapper, "effective_mapping", _empty_mapping)
    statuses, links = mapper.build_mapping(controls, verdicts)
    assert statuses == {}
    assert links == []


def test_mapper_request_frameworks():
    request = ControlMappingRequest(
        verdict_id="v1", framework_ids=["pci_dss_4.0"], engagement_id="e1"
    )
    assert mapper.request_frameworks(request, ["nist_csf_2.0"]) == ["pci_dss_4.0"]
    empty = ControlMappingRequest(verdict_id="v1", framework_ids=[], engagement_id="e1")
    assert mapper.request_frameworks(empty, ["nist_csf_2.0"]) == ["nist_csf_2.0"]


@pytest.mark.asyncio
async def test_repository_list_controls_for_techniques(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        found = await repository.list_controls_for_techniques(
            session, ["T1078"], ["nist_csf_2.0"]
        )
    assert [c.control_id for c in found] == ["DE.CM-01"]
    async with db_session_factory() as session:
        none = await repository.list_controls_for_techniques(
            session, ["T1578"], ["iso_27001_2022"]
        )
    assert none == []


@pytest.mark.asyncio
async def test_repository_upsert_and_get_control_statuses(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "cm-repo-001"
    async with db_session_factory() as session:
        await repository.upsert_control_statuses(
            session, engagement_id, {"DE.CM-01": "Met"}, {"DE.CM-01": "h1"}
        )
        await repository.upsert_control_statuses(
            session, engagement_id, {"DE.CM-01": "Not Met"}, {"DE.CM-01": "h2"}
        )
        statuses = await repository.get_control_statuses(session, engagement_id)
    assert statuses == {"DE.CM-01": "Not Met"}


@pytest.mark.asyncio
async def test_repository_list_controls_by_id(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    async with db_session_factory() as session:
        found = await repository.list_controls_by_id(session, ["DE.AE-02", "DE.CM-01"])
        missing = await repository.list_controls_by_id(session, ["no-such-ctrl"])
    assert {c.control_id for c in found} == {"DE.AE-02", "DE.CM-01"}
    assert missing == []


def _verdicts_for_hash_map():
    return [
        _verdict("v1", "T1486", "Detected", "h-a"),
        _verdict("v2", "T1490", "Detected", "h-b"),
        _verdict("v3", "T1078", "No Data", "h-c"),
    ]


def test_repository_evidence_hash_map():
    test_controls = [
        _control("DE.AE-02", ["T1486", "T1490"]),
        _control("DE.CM-01", ["T1078", "T1098"]),
    ]
    verdicts = _verdicts_for_hash_map()
    met_map = repository.evidence_hash_map(
        {"DE.AE-02": "Met", "DE.CM-01": "Not Met"}, verdicts, test_controls
    )
    assert met_map["DE.AE-02"] == "h-a"
    assert met_map["DE.CM-01"] == "h-c"


def test_repository_evidence_hash_for_control():
    control = _control("DE.AE-02", ["T1486", "T1490"])
    assert (
        repository.evidence_hash_for_control(control, _verdicts_for_hash_map()) == "h-a"
    )
    assert (
        repository.evidence_hash_for_control(
            _control("GDPR-Art32", ["T1566"]), _verdicts_for_hash_map()
        )
        is None
    )


async def _seed_engagement(
    factory: async_sessionmaker[AsyncSession],
    engagement_id: str,
) -> None:
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'E2E', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await session.execute(
            text(
                "INSERT INTO verdicts "
                "(verdict_id, engagement_id, technique_id, outcome, severity_id, evidence_hash) "
                "VALUES (:vid, :e, 'T1078', 'Detected', 1, "
                "'a3f5c2d1e8b4a7f0c9d2e5b8a1f4c7d0e3b6a9f2c5d8e1b4a7f0c3d6e9b2a5f8')"
            ),
            {"vid": f"{engagement_id}-vrd-0000", "e": engagement_id},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_map_controls_endpoint(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "cm-e2e-001"
    await _seed_engagement(db_session_factory, engagement_id)

    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/map-controls",
            json={
                "verdict_id": f"{engagement_id}-vrd-0000",
                "framework_ids": ["nist_csf_2.0"],
                "engagement_id": engagement_id,
            },
        )
        body = resp.json()
    assert resp.status_code == 200
    assert body["engagement_id"] == engagement_id
    assert body["control_statuses"]["DE.CM-01"] == "Met"
    assert body["coverage_pct"] == 100.0


@pytest.mark.asyncio
async def test_map_controls_verdict_not_found():
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/map-controls",
            json={
                "verdict_id": "no-verdict",
                "framework_ids": ["nist_csf_2.0"],
                "engagement_id": "cm-e2e-001",
            },
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_map_controls_engagement_not_found(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "cm-e2e-002"
    await _seed_engagement(db_session_factory, engagement_id)
    async with make_client(app) as client:
        resp = await client.post(
            "/api/v1/map-controls",
            json={
                "verdict_id": f"{engagement_id}-vrd-0000",
                "framework_ids": ["nist_csf_2.0"],
                "engagement_id": "cm-no-eng",
            },
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_control_statuses_endpoint(
    db_session_factory: async_sessionmaker[AsyncSession],
):
    engagement_id = "cm-st-001"
    async with db_session_factory() as session:
        await session.execute(
            text(
                "INSERT INTO engagements (engagement_id, name, organization, frameworks) "
                "VALUES (:e, 'St', 'CyArt', ARRAY['nist_csf_2.0'])"
                " ON CONFLICT (engagement_id) DO NOTHING"
            ),
            {"e": engagement_id},
        )
        await repository.upsert_control_statuses(
            session, engagement_id, {"DE.CM-01": "Met"}, {"DE.CM-01": "h1"}
        )
        await session.commit()

    async with make_client(app) as client:
        resp = await client.get(f"/api/v1/control-statuses/{engagement_id}")
        body = resp.json()
    assert resp.status_code == 200
    assert body["control_statuses"]["DE.CM-01"] == "Met"
    assert body["framework_ids"] == ["nist_csf_2.0"]


def test_mapped_control_status_worst_weight_preserved():
    grouped = {"T1490": {"Missed"}, "T1486": {"Detected"}}
    status = mapper.mapped_control_status(
        ["T1490", "T1486"], {"T1490", "T1486"}, grouped
    )
    assert status == "Not Met"


def test_evidence_hash_map_skips_controls_without_status():
    controls = [
        Control(
            control_id="PR.AC-01",
            framework_id="nist_csf_2.0",
            category="PR",
            name="Access control",
            description="desc",
            attack_mapping=["T1486"],
        )
    ]
    verdicts = [{"technique_id": "T1486", "outcome": "Detected", "evidence_hash": "h1"}]
    result = repository.evidence_hash_map({}, verdicts, controls)
    assert "PR.AC-01" not in result
