"""End-to-end integration test suite verifying:

1. Complete Pulsar portion of M2 -> M3 flow
2. API & Data flow across FastAPI endpoints
3. Pulsar output reaching Quasar (Resilience Scorer) and driving the score calculation
4. Validation and error handling on corrupted / malformed M2 events
"""

import asyncio
import json
import sqlite3
import sys
from collections.abc import AsyncGenerator
from typing import Any, cast

import httpx
from httpx import ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.evidence_aggregator.main import app as pulsar_app
from apps.evidence_aggregator.main import get_session as pulsar_get_session
from apps.resilience_scorer.compute import assemble_score
from apps.resilience_scorer.main import app as quasar_app
from apps.resilience_scorer.main import get_session as quasar_get_session
from apps.shared.ocsf import (
    event_problems,
    evidence_hash,
    outcome_from_disposition,
    technique_id_from_event,
    validate_events,
)

# Register SQLite adapters so list and dict parameters can be bound cleanly
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

pass_count = 0
fail_count = 0


def report(test_name: str, passed: bool, detail: str = "") -> None:
    global pass_count, fail_count
    icon = "PASS" if passed else "FAIL"
    if passed:
        pass_count += 1
    else:
        fail_count += 1
    extra = f" => {detail}" if detail else ""
    print(f"  [{icon}] {test_name}{extra}")


SAMPLE_EVENTS: list[dict[str, Any]] = [
    {
        "class_uid": 3002,
        "class_name": "Authentication",
        "category_uid": 3,
        "category_name": "Identity & Access Management",
        "activity_id": 1,
        "activity_name": "Logon",
        "severity_id": 1,
        "severity": "Informational",
        "type_uid": 300201,
        "type_name": "Authentication: Logon",
        "time": 1727273400000,
        "disposition": "Allowed",
        "metadata": {
            "version": "1.1.0",
            "product": {"name": "Cybreach Auth Engine", "vendor_name": "Cybreach"},
        },
        "user": {"name": "sneha", "uid": "usr_9921", "type": "User"},
        "src_endpoint": {"ip": "192.168.1.105", "port": 54321},
        "status_id": 1,
        "status": "Success",
    },
    {
        "class_uid": 2001,
        "class_name": "Security Finding",
        "category_uid": 2,
        "category_name": "Findings",
        "activity_id": 1,
        "activity_name": "Create",
        "severity_id": 4,
        "severity": "High",
        "type_uid": 200101,
        "time": 1727273405000,
        "disposition": "Detected",
        "metadata": {
            "version": "1.1.0",
            "product": {"name": "Cybreach EDR", "vendor_name": "Cybreach"},
        },
        "attacks": [
            {
                "technique": {
                    "uid": "T1059.001",
                    "name": "Command and Scripting Interpreter: PowerShell",
                },
                "tactic": {"name": "Execution", "uid": "TA0002"},
            }
        ],
        "finding_info": {
            "title": "Suspicious PowerShell execution with encoded command",
            "desc": "PowerShell executed with -EncodedCommand parameter",
            "types": ["T1059.001"],
        },
        "status_id": 1,
        "status": "New",
    },
    {
        "class_uid": 3002,
        "class_name": "Authentication",
        "category_uid": 3,
        "category_name": "Identity & Access Management",
        "activity_id": 1,
        "activity_name": "Logon",
        "severity_id": 2,
        "severity": "Low",
        "type_uid": 300201,
        "type_name": "Authentication: Logon",
        "time": 1727273410000,
        "disposition": "Missed",
        "metadata": {"version": "1.1.0"},
        "status_id": 2,
        "status": "Failure",
    },
]

BAD_EVENTS: list[dict[str, Any]] = [
    {
        "class_uid": "3002",
        "activity_id": "ONE",
        "metadata": {"version": "1.1.0"},
    },
    {
        "severity_id": 2,
        "metadata": {"version": "1.1.0"},
    },
    {
        "class_uid": 3002,
        "type_uid": 300201,
        "severity_id": 99,
        "metadata": {"version": "1.1.0"},
    },
]


def _verify_ocsf() -> list[str]:
    print("\n[SECTION 1] Pulsar OCSF Ingestion & Normalization")
    try:
        validated = validate_events(SAMPLE_EVENTS)
        report(
            "OCSF validate_events passes on valid sample dataset",
            len(validated) == 3,
            f"{len(validated)} events validated",
        )
    except Exception as e:
        report("OCSF validate_events", False, str(e))

    for idx, bad_evt in enumerate(BAD_EVENTS, start=1):
        problems = event_problems(bad_evt)
        report(
            f"OCSF rejects malformed Category 4 case {idx}",
            len(problems) > 0,
            f"Identified error: {problems[0]}",
        )

    t1 = technique_id_from_event(SAMPLE_EVENTS[0])
    report(
        "Technique ID extracted for Cat 1 (default fallback)",
        t1 == "T1078",
        f"technique={t1}",
    )

    t2 = technique_id_from_event(SAMPLE_EVENTS[1])
    report(
        "Technique ID extracted for Cat 2 (attacks list T1059.001 - ANOMALY FIX)",
        t2 == "T1059.001",
        f"technique={t2}",
    )

    outcomes = [
        outcome_from_disposition(cast("str | None", e.get("disposition")))
        for e in SAMPLE_EVENTS
    ]
    report(
        "Dispositions mapped to outcomes correctly",
        outcomes == ["Detected", "Detected", "Missed"],
        f"outcomes={outcomes}",
    )

    hashes = [evidence_hash(e) for e in SAMPLE_EVENTS]
    report(
        "Deterministic SHA-256 evidence hashes generated",
        all(len(h) == 64 for h in hashes) and len(set(hashes)) == 3,
        f"3 unique hashes generated (sample: {hashes[0][:16]}...)",
    )
    return hashes


async def _verify_pulsar_api(
    client: httpx.AsyncClient, engagement_id: str, hashes: list[str]
) -> list[str]:
    print("\n[SECTION 2] Pulsar API Endpoints & Verdict Persistence")
    r = await client.get("/health")
    report(
        "Pulsar GET /health responds 200 OK",
        r.status_code == 200 and r.json().get("service") == "evidence-aggregator",
    )

    ingest_payload = {
        "engagement_id": engagement_id,
        "name": "Integration Assessment",
        "organization": "CyBreach Assurance Lab",
        "frameworks": ["nist_csf_2.0", "iso_27001_2022"],
        "events": SAMPLE_EVENTS,
    }
    r = await client.post("/api/v1/ingest-ocsf", json=ingest_payload)
    report(
        "Pulsar POST /api/v1/ingest-ocsf persists verdicts",
        r.status_code == 201 and r.json().get("ingested") == 3,
        f"verdict_ids={r.json().get('verdict_ids')}",
    )
    verdict_ids = cast("list[str]", r.json().get("verdict_ids", []))

    r_idemp = await client.post("/api/v1/ingest-ocsf", json=ingest_payload)
    report(
        "Pulsar POST /api/v1/ingest-ocsf is idempotent (skips duplicates)",
        r_idemp.status_code == 201 and r_idemp.json().get("ingested") == 0,
        "0 duplicates inserted",
    )

    r = await client.get(f"/api/v1/verdicts/{engagement_id}/engagement")
    verdicts = r.json()
    report(
        "Pulsar GET /api/v1/verdicts/... returns all verdicts",
        r.status_code == 200 and len(verdicts) == 3,
        f"Retrieved {len(verdicts)} verdicts",
    )

    link1 = {
        "link_id": "lnk-001",
        "control_id": "DE.AE-02",
        "verdict_id": verdict_ids[0],
        "evidence_hash": hashes[0],
        "chain_position": 1,
    }
    link2 = {
        "link_id": "lnk-002",
        "control_id": "PR.AC-01",
        "verdict_id": verdict_ids[1],
        "evidence_hash": hashes[1],
        "chain_position": 1,
    }
    r1 = await client.post("/api/v1/evidence-links", json=link1)
    r2 = await client.post("/api/v1/evidence-links", json=link2)
    report(
        "Pulsar POST /api/v1/evidence-links persists evidence links",
        r1.status_code == 201 and r2.status_code == 201,
    )

    r = await client.get(f"/api/v1/evidence-summary/{engagement_id}")
    summary = r.json()
    report(
        "Pulsar GET /api/v1/evidence-summary calculates completeness",
        r.status_code == 200 and summary["total_links"] == 2,
        f"unique_hashes={summary['unique_hashes']}",
    )

    bad_payload = {
        "engagement_id": "ENG-BAD",
        "events": [BAD_EVENTS[0]],
    }
    r_bad = await client.post("/api/v1/ingest-ocsf", json=bad_payload)
    report(
        "Pulsar POST /api/v1/ingest-ocsf rejects bad data with HTTP 422",
        r_bad.status_code == 422,
        "Malformed event rejected cleanly",
    )
    return verdict_ids


async def _verify_quasar_api(client: httpx.AsyncClient, engagement_id: str) -> None:
    print("\n[SECTION 3] Verify Pulsar Output Reaches Quasar (Resilience Scorer)")
    r = await client.get("/health")
    report(
        "Quasar GET /health responds 200 OK",
        r.status_code == 200 and r.json().get("service") == "resilience-scorer",
    )

    score_req = {
        "engagement_id": engagement_id,
        "framework_ids": ["nist_csf_2.0", "iso_27001_2022"],
    }
    r = await client.post("/api/v1/calculate-score", json=score_req)
    report(
        "Quasar POST /api/v1/calculate-score successfully executed",
        r.status_code == 200,
        f"score_id={r.json().get('score_id')}",
    )
    score_data = r.json()

    report(
        "Quasar detection_score matches Pulsar detected verdicts ratio",
        abs(score_data["detection_score"] - 66.7) < 0.2,
        f"detection_score={score_data['detection_score']} (2 Detected / 3 Total)",
    )
    report(
        "Quasar evidence_score matches Pulsar unique evidence hashes ratio",
        abs(score_data["evidence_score"] - 66.7) < 0.2,
        f"evidence_score={score_data['evidence_score']} (2 Linked / 3 Expected)",
    )
    report(
        "Quasar composite score computed correctly (40% cov + 35% det + 25% evi)",
        abs(score_data["composite_score"] - 66.7) < 0.2,
        f"composite={score_data['composite_score']}",
    )
    report(
        "Quasar resilience band reflects Pulsar input telemetry",
        score_data["band"] == "Moderate",
        f"band={score_data['band']}",
    )

    r = await client.get(f"/api/v1/scores/{engagement_id}")
    scores = r.json()
    report(
        "Quasar GET /api/v1/scores/... returns persisted score history",
        r.status_code == 200 and len(scores) >= 1,
        f"Stored {len(scores)} historical score records",
    )

    r_blast = await client.post(
        "/api/v1/blast-radius",
        json={
            "asset_id": "srv-prod-db-01",
            "exposure": "external",
            "criticality": "high",
            "internet_facing": True,
        },
    )
    report(
        "Quasar POST /api/v1/blast-radius computes asset blast radius",
        r_blast.status_code == 200 and r_blast.json()["blast_radius_score"] == 100.0,
        f"blast_radius_score={r_blast.json()['blast_radius_score']}",
    )

    r_risk = await client.post(
        "/api/v1/weighted-risk",
        json={
            "cve_id": "CVE-2026-1059",
            "cvss": 9.0,
            "epss": 0.85,
            "blast_radius": 100.0,
        },
    )
    report(
        "Quasar POST /api/v1/weighted-risk combines CVSS + EPSS + Blast Radius",
        r_risk.status_code == 200 and r_risk.json()["final_score"] == 90.5,
        f"final_score={r_risk.json()['final_score']}, band={r_risk.json()['band']}",
    )


def _verify_sensitivity() -> None:
    print("\n[SECTION 4] Data Flow Sensitivity: Proving Pulsar Drives Quasar")
    score_resilient = assemble_score(
        score_id="ENG-RESILIENT-scr-0001",
        engagement_id="ENG-RESILIENT",
        statuses={"C1": "Met", "C2": "Met", "C3": "Met"},
        total_verdicts=3,
        detected_verdicts=3,
        linked_events=3,
        expected_events=3,
    )
    report(
        "When Pulsar achieves 100% detection & evidence, Quasar reaches Resilient",
        score_resilient.composite_score == 100.0
        and score_resilient.band == "Resilient",
        f"composite={score_resilient.composite_score}, band={score_resilient.band}",
    )

    score_critical = assemble_score(
        score_id="ENG-CRITICAL-scr-0001",
        engagement_id="ENG-CRITICAL",
        statuses={"C1": "Not Met", "C2": "Not Met", "C3": "Not Met"},
        total_verdicts=3,
        detected_verdicts=0,
        linked_events=0,
        expected_events=3,
    )
    report(
        "When Pulsar has 0% detection & evidence, Quasar drops to 0.0 Critical",
        score_critical.composite_score == 0.0 and score_critical.band == "Critical",
        f"composite={score_critical.composite_score}, band={score_critical.band}",
    )


async def _init_db(engine: Any) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
            CREATE TABLE engagements (
                engagement_id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(255),
                organization VARCHAR(255),
                frameworks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE TABLE verdicts (
                verdict_id VARCHAR(128) PRIMARY KEY,
                engagement_id VARCHAR(64),
                technique_id VARCHAR(64),
                outcome VARCHAR(32),
                severity_id INTEGER,
                evidence_hash VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE TABLE evidence_links (
                link_id VARCHAR(196) PRIMARY KEY,
                control_id VARCHAR(64),
                verdict_id VARCHAR(128),
                evidence_hash VARCHAR(64),
                chain_position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE TABLE control_statuses (
                engagement_id VARCHAR(64),
                control_id VARCHAR(64),
                status VARCHAR(32),
                evidence_hash VARCHAR(64),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (engagement_id, control_id)
            );
        """
            )
        )
        await conn.execute(
            text(
                """
            CREATE TABLE resilience_scores (
                score_id VARCHAR(128) PRIMARY KEY,
                engagement_id VARCHAR(64),
                composite FLOAT,
                coverage FLOAT,
                detection FLOAT,
                evidence FLOAT,
                band VARCHAR(32),
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
            )
        )


async def run_integration_suite() -> bool:
    print("=" * 70)
    print("  M2 -> PULSAR -> QUASAR INTEGRATION VERIFICATION SUITE")
    print("  CyBreach Module 3 Assurance Pipeline")
    print("=" * 70)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    await _init_db(engine)

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    pulsar_app.dependency_overrides[pulsar_get_session] = override_session
    quasar_app.dependency_overrides[quasar_get_session] = override_session

    engagement_id = "ENG-PULSAR-QUASAR-001"
    hashes = _verify_ocsf()

    async with httpx.AsyncClient(
        transport=ASGITransport(app=pulsar_app), base_url="http://test"
    ) as p_client:
        await _verify_pulsar_api(p_client, engagement_id, hashes)

    async with session_factory() as session:
        await session.execute(
            text(
                """
            INSERT INTO control_statuses (
                engagement_id, control_id, status, evidence_hash
            )
            VALUES (:eng, 'DE.AE-02', 'Met', :h1),
                   (:eng, 'PR.AC-01', 'Met', :h2),
                   (:eng, 'DE.CM-01', 'Not Met', NULL)
        """
            ),
            {"eng": engagement_id, "h1": hashes[0], "h2": hashes[1]},
        )
        await session.commit()

    async with httpx.AsyncClient(
        transport=ASGITransport(app=quasar_app), base_url="http://test"
    ) as q_client:
        await _verify_quasar_api(q_client, engagement_id)

    _verify_sensitivity()

    print("\n" + "=" * 70)
    total_tests = pass_count + fail_count
    print(f"  INTEGRATION TEST SUMMARY: {pass_count}/{total_tests} passed")
    if fail_count == 0:
        print("  STATUS: PULSAR -> QUASAR M2-M3 INTEGRATION VERIFIED SUCCESSFULLY!")
    else:
        print(f"  STATUS: {fail_count} FAILURES DETECTED")
    print("=" * 70)

    return fail_count == 0


if __name__ == "__main__":
    success = asyncio.run(run_integration_suite())
    sys.exit(0 if success else 1)
