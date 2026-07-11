"""Tests for build_attack_mapping.py"""

import json
from pathlib import Path

import pytest

from apps.framework_registry import build_attack_mapping as bam


def test_load_attack_data(tmp_path: Path) -> None:
    data = {"mappings": {"AC-03": ["T1548", "T1611"]}}
    fpath: Path = tmp_path / "attack.json"
    fpath.write_text(json.dumps(data))
    result = bam.load_attack_data(fpath)
    assert result["AC-03"] == ["T1548", "T1611"]


def test_load_crosswalk_raises_not_implemented(tmp_path: Path) -> None:
    fpath: Path = tmp_path / "crosswalk.json"
    fpath.write_text("{}")
    with pytest.raises(NotImplementedError):
        bam.load_crosswalk(fpath)


def test_build_full_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bam, "load_crosswalk", lambda path: {"CTRL-1": ["AC-03"]})

    csf_path: Path = tmp_path / "csf.json"
    csf_path.write_text(
        json.dumps(
            {
                "controls": [
                    {"control_id": "CTRL-1"},
                    {"control_id": "CTRL-2"},
                ]
            }
        )
    )
    crosswalk_path: Path = tmp_path / "crosswalk.json"
    crosswalk_path.write_text("{}")
    attack_path: Path = tmp_path / "attack.json"
    attack_path.write_text(json.dumps({"mappings": {"AC-03": ["T1548", "T1611"]}}))
    out_path: Path = tmp_path / "out.json"

    bam.build(csf_path, crosswalk_path, attack_path, out_path)

    result = json.loads(out_path.read_text())
    assert result["controls"][0]["attack_mapping"] == ["T1548", "T1611"]
    assert result["controls"][1]["attack_mapping"] == []
