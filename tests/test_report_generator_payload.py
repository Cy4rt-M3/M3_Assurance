"""Tests for the M3 -> CYART report payload mapper."""

from datetime import UTC, datetime
from typing import Any

from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.report_generator.payload import (
    build_findings,
    build_recommendations,
    build_report_data,
    build_statistics,
    cvss_for_severity,
    overall_risk_from_statistics,
    severity_for_priority,
)
from apps.resilience_scorer.models import ResilienceScore

GENERATED = datetime(2026, 9, 20, 9, 30, tzinfo=UTC)


def _engagement() -> dict[str, Any]:
    return {
        "engagement_id": "eng-alpha-001",
        "name": "Internal Security Assessment",
        "organization": "CYART",
        "frameworks": ["nist_csf_2_0_2", "iso_27001_2022"],
    }


def _score(band: str = "Resilient") -> ResilienceScore:
    return ResilienceScore(
        score_id="scr-1",
        engagement_id="eng-alpha-001",
        composite_score=88.0,
        coverage_score=90.0,
        detection_score=85.0,
        evidence_score=82.0,
        band=band,
    )


def _gap(priority: int, control_id: str = "DE.AE-02") -> GapAnalysis:
    return GapAnalysis(
        analysis_id=f"gap-{control_id}-{priority}",
        engagement_id="eng-alpha-001",
        control_id=control_id,
        gap_type="missed_detection",
        priority=priority,
        remediation=f"Fix {control_id}",
    )


def test_severity_for_priority():
    assert severity_for_priority(1) == "critical"
    assert severity_for_priority(2) == "high"
    assert severity_for_priority(3) == "medium"
    assert severity_for_priority(4) == "low"
    assert severity_for_priority(5) == "informational"
    assert severity_for_priority(0) == "informational"


def test_cvss_for_severity():
    assert cvss_for_severity("critical") == 9.8
    assert cvss_for_severity("high") == 8.4
    assert cvss_for_severity("medium") == 5.6
    assert cvss_for_severity("low") == 3.1
    assert cvss_for_severity("informational") == 1.5
    assert cvss_for_severity("bogus") == 1.5


def test_overall_risk_from_statistics_thresholds():
    assert overall_risk_from_statistics({"critical": 0, "high": 0, "medium": 0, "low": 0}) == "Low"
    assert overall_risk_from_statistics({"critical": 0, "high": 0, "medium": 6, "low": 0}) == "Medium"
    assert overall_risk_from_statistics({"critical": 0, "high": 5, "medium": 0, "low": 0}) == "High"
    assert overall_risk_from_statistics({"critical": 3, "high": 0, "medium": 0, "low": 0}) == "Critical"


def test_build_findings_orders_by_priority():
    findings = build_findings([_gap(3), _gap(1)], ["nist_csf_2_0_2"])
    assert findings[0]["severity"] == "critical"
    assert findings[0]["finding_id"] == "gap-DE.AE-02-1"
    assert findings[1]["severity"] == "medium"
    assert findings[0]["remediation"] == "Fix DE.AE-02"
    assert findings[0]["cvss_score"] == 9.8
    assert "missed_detection" in findings[0]["title"]
    assert findings[0]["status"] == "Open"


def test_build_findings_empty():
    assert build_findings([], []) == []


def test_build_statistics_counts_and_average():
    findings = [
        {"severity": "Critical", "cvss_score": 8.0},
        {"severity": "high", "cvss_score": 8.0},
        {"severity": "Medium", "cvss_score": 8.0},
        {"severity": "informational", "cvss_score": 8.0},
    ]
    stats = build_statistics(findings)
    assert stats["critical"] == 1
    assert stats["high"] == 1
    assert stats["medium"] == 1
    assert stats["informational"] == 1
    assert stats["average_cvss"] == 8.0


def test_build_statistics_skips_invalid_cvss():
    stats = build_statistics([{"severity": "low", "cvss_score": "nope"}])
    assert stats["low"] == 1
    assert stats["average_cvss"] == 0.0


def test_build_statistics_empty():
    assert build_statistics([])["average_cvss"] == 0.0


def test_build_recommendations_skips_informational():
    findings = [
        {"severity": "Critical"},
        {"severity": "High"},
        {"severity": "Medium"},
        {"severity": "informational"},
    ]
    recs = build_recommendations(findings)
    assert [r["priority"] for r in recs] == [1, 2, 3]
    assert recs[0]["title"] == "Immediate Remediation Required"
    assert build_recommendations([]) == []


def test_build_report_data_full_payload():
    data = build_report_data(
        engagement=_engagement(),
        score=_score(),
        statuses={"DE.AE-02": "Met"},
        controls=[Control(
            control_id="DE.AE-02",
            framework_id="nist_csf_2_0_2",
            category="Detect",
            name="AED 02",
            description="Detects events",
            attack_mapping=["T1486"],
        )],
        verdicts=[{"verdict_id": "v1", "technique_id": "T1486", "outcome": "Detected"}],
        gaps=[_gap(1)],
        report_id="RPT-0001",
        generated_at=GENERATED,
    )
    assert data["cover"]["title"] == "CYART Security Assessment Report"
    assert data["cover"]["report_id"] == "RPT-0001"
    assert isinstance(data["cover"]["generated_at"], datetime)
    assert data["organization"]["name"] == "CYART"
    assert data["scope"]["framework"] == "nist_csf_2_0_2, iso_27001_2022"
    assert data["scope"]["assessment_period"] == "September 2026"
    assert data["findings"][0]["severity"] == "critical"
    assert data["statistics"]["critical"] == 1
    assert data["risk_matrix"]["Critical"] == 1
    assert data["executive_summary"]["overall_risk"] == "Low"
    assert data["executive_summary"]["total_findings"] == 1
    assert "organizational risk is Low" in data["executive_summary"]["summary_text"]
    assert data["risk_matrix"]["High"] == 0
    assert data["recommendations"][0]["priority"] == 1
    assert data["compliance_mapping"] == [
        {"framework": "nist_csf_2_0_2, iso_27001_2022", "control": "DE.AE-02"}
    ]
    assert data["appendix"]["classification"] == "Confidential"
    assert data["references"] == [
        "OWASP Top 10",
        "NIST Cyber Security Framework",
        "MITRE ATT&CK",
        "CIS Controls",
    ]
    assert data["footer"]["copyright"] == "\u00a9 2026 CYART"
    assert data["dashboard"] == data["statistics"]


def test_build_report_data_no_score_no_findings():
    data = build_report_data(
        engagement={"engagement_id": "e2", "name": "Blank", "organization": "Org", "frameworks": []},
        score=None,
        statuses={},
        controls=[],
        verdicts=[],
        gaps=[],
        report_id="RPT-0002",
        generated_at=GENERATED,
    )
    assert data["findings"] == []
    assert data["statistics"]["average_cvss"] == 0.0
    assert data["executive_summary"]["overall_risk"] == "Low"
    assert data["executive_summary"]["summary_text"].startswith(
        "The assessment did not identify any actionable findings"
    )
    assert data["compliance_mapping"] == []
    assert data["recommendations"] == []
    assert data["scope"]["framework"] == "NIST Cyber Security Framework"
    assert data["risk_matrix"]["Critical"] == 0


def test_build_report_data_band_maps_to_risk():
    data = build_report_data(
        engagement=_engagement(),
        score=_score("At Risk"),
        statuses={},
        controls=[],
        verdicts=[],
        gaps=[_gap(2), _gap(1)],
        report_id="RPT-0003",
        generated_at=GENERATED,
    )
    assert data["executive_summary"]["overall_risk"] == "High"
    assert len(data["compliance_mapping"]) == 2