"""Tests for the pipeline orchestrator and CLI."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import apps.framework_registry.seed as seed_module
import apps.pipeline.__main__ as cli
from apps.pipeline.engine import run_pipeline


def _ocsf_event(
    disposition: str,
    technique: str,
    severity_id: int = 1,
) -> dict[str, object]:
    return {
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
        "attack": {"technique_uid": technique},
    }


@pytest.mark.asyncio
async def test_run_pipeline_end_to_end():
    engagement_id = "pipe-e2e-001"
    result = await run_pipeline(
        engagement_id=engagement_id,
        name="Pipeline E2E",
        organization="CyArt",
        events=[
            _ocsf_event("Allowed", "T1486"),
            _ocsf_event("Missed", "T1078"),
        ],
        frameworks=["nist_csf_2.0"],
    )
    assert result["engagement_id"] == engagement_id
    assert len(result["verdict_ids"]) == 2
    statuses = result["control_statuses"]
    assert statuses["DE.AE-02"] == "Met"
    assert statuses["RS.MI-01"] == "Met"
    assert statuses["DE.CM-01"] == "Not Met"
    assert result["score"]["engagement_id"] == engagement_id
    assert result["score"]["band"] == "At Risk"
    assert len(result["gaps"]) >= 1
    assert any(g["gap_type"] == "missed_detection" for g in result["gaps"])
    assert len(result["report"]["content_hash"]) == 64


@pytest.mark.asyncio
async def test_run_pipeline_is_idempotent():
    engagement_id = "pipe-e2e-002"
    events = [_ocsf_event("Allowed", "T1486", severity_id=3)]
    first = await run_pipeline(
        engagement_id=engagement_id,
        name="Idempotent",
        organization="CyArt",
        events=events,
        frameworks=["nist_csf_2.0"],
    )
    second = await run_pipeline(
        engagement_id=engagement_id,
        name="Idempotent",
        organization="CyArt",
        events=events,
        frameworks=["nist_csf_2.0"],
    )
    assert first["score"]["score_id"] == f"{engagement_id}-scr-0001"
    assert second["score"]["score_id"] == f"{engagement_id}-scr-0002"
    assert second["report"]["report_id"] == f"{engagement_id}-rpt-0002"
    assert second["control_statuses"] == first["control_statuses"]


def test_cli_parse_args_defaults():
    args = cli.parse_args(["events.json"])
    assert args.engagement_id == "ENG-2026-001"
    assert args.name == "SOC Pen Test 2026"
    assert args.organization == "CyberLab Corp"
    assert args.frameworks is None
    assert args.no_seed is False


def test_cli_parse_args_custom():
    args = cli.parse_args(
        [
            "events.json",
            "--engagement-id",
            "ENG-X",
            "--framework",
            "gdpr_regulation_eu_2016_679",
            "--no-seed",
        ]
    )
    assert args.engagement_id == "ENG-X"
    assert list(args.frameworks) == ["gdpr_regulation_eu_2016_679"]
    assert args.no_seed is True


def test_cli_load_events_ok(tmp_path: Path):
    path = tmp_path / "events.json"
    path.write_text(json.dumps([{"class_uid": 4001}]))
    assert cli.load_events(path) == [{"class_uid": 4001}]


def test_cli_load_events_invalid(tmp_path: Path):
    path = tmp_path / "events.json"
    path.write_text("[]")
    with pytest.raises(ValueError):
        cli.load_events(path)
    path.write_text("{not json")
    with pytest.raises(json.JSONDecodeError):
        cli.load_events(path)


@pytest.mark.asyncio
async def test_cli_main_success_no_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "events.json"
    path.write_text(json.dumps([{"class_uid": 4001}]))

    captured: dict[str, object] = {}

    async def fake_run_pipeline(**kwargs: dict[str, Any]) -> dict[str, object]:
        captured.update(kwargs)
        return {"engagement_id": kwargs["engagement_id"], "score": {}}

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    code = await cli.main([str(path), "--no-seed"])
    assert code == 0
    assert captured["frameworks"] == cli.DEFAULT_FRAMEWORKS
    assert captured["organization"] == "CyberLab Corp"


@pytest.mark.asyncio
async def test_cli_main_success_with_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    db_session_factory: async_sessionmaker[AsyncSession],
):
    path = tmp_path / "events.json"
    path.write_text(json.dumps([{"class_uid": 4001}]))

    async def fake_seed(_factory: async_sessionmaker[AsyncSession]) -> tuple[int, int]:
        return (1, 1)

    monkeypatch.setattr(
        seed_module, "build_session_factory_from_settings", lambda: db_session_factory
    )
    monkeypatch.setattr(seed_module, "seed", fake_seed)

    async def fake_run_pipeline(**kwargs: dict[str, Any]) -> dict[str, object]:
        return {"engagement_id": kwargs["engagement_id"]}

    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)
    code = await cli.main([str(path)])
    assert code == 0


@pytest.mark.asyncio
async def test_cli_main_missing_file(tmp_path: Path):
    code = await cli.main([str(tmp_path / "does-not-exist.json")])
    assert code == 2


def test_cli_run_entrypoint(monkeypatch: pytest.MonkeyPatch):
    async def fake_main(argv: list[str]) -> int:
        return 0

    monkeypatch.setattr(cli, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["app", "events.json"])
    with pytest.raises(SystemExit) as exc:
        cli.run()
    assert exc.value.code == 0
