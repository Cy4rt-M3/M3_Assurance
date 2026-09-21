"""Map M3 service data into the CYART-compatible report payload shape.

The reference pentest-report layout (port of the ``nebula`` branch
``renderer/pdf_renderer.py``) consumes one JSON-serializable dict whose
sections are: cover, organization, scope, methodology, assets, findings,
statistics, risk_matrix, recommendations, appendix, references,
compliance_mapping, footer and executive_summary.

This module translates the M3 engagement data (control statuses,
resilience score and gap analysis) into exactly that shape so the shared
renderer can stay fully decoupled from the domain models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from apps.framework_registry.models import Control
from apps.gap_analyzer.models import GapAnalysis
from apps.resilience_scorer.models import ResilienceScore

DEFAULT_METHODOLOGY_PHASES = [
    "Planning",
    "Reconnaissance",
    "Vulnerability Assessment",
    "Manual Validation",
    "Risk Analysis",
    "Reporting",
]

DEFAULT_TOOLS = ["Nmap", "Nessus", "Burp Suite Professional", "OWASP ZAP"]

DEFAULT_REFERENCES = [
    "OWASP Top 10",
    "NIST Cyber Security Framework",
    "MITRE ATT&CK",
    "CIS Controls",
]

PRIORITY_SEVERITY = {1: "critical", 2: "high", 3: "medium", 4: "low"}

SEVERITY_CVSS = {
    "critical": 9.8,
    "high": 8.4,
    "medium": 5.6,
    "low": 3.1,
    "informational": 1.5,
}

SEVERITY_TITLES = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "informational": "Informational",
}

BAND_RISK = {
    "Critical": "Critical",
    "At Risk": "High",
    "Moderate": "Medium",
    "Strong": "Low",
    "Resilient": "Low",
}

RECOMMENDATION_TEMPLATES = {
    "critical": (
        "Immediate Remediation Required",
        "Resolve this Critical vulnerability immediately.",
    ),
    "high": (
        "High Risk Remediation",
        "Patch this High severity vulnerability as soon as possible.",
    ),
    "medium": (
        "Medium Risk Remediation",
        "Schedule remediation during the next maintenance window.",
    ),
    "low": (
        "Low Risk Improvement",
        "Address this issue as part of routine security improvements.",
    ),
}


def severity_for_priority(priority: int) -> str:
    """Map a M3 gap priority (1=Critical .. 5=Informational) to a severity key."""
    return PRIORITY_SEVERITY.get(int(priority), "informational")


def cvss_for_severity(severity: str) -> float:
    """Default CVSS-style score for a severity band (presentation placeholder)."""
    return SEVERITY_CVSS.get(severity, SEVERITY_CVSS["informational"])


def overall_risk_from_statistics(statistics: dict[str, Any]) -> str:
    """Score posture from severity counts, mirroring the reference engine."""
    critical = int(statistics.get("critical", 0) or 0)
    high = int(statistics.get("high", 0) or 0)
    medium = int(statistics.get("medium", 0) or 0)
    low = int(statistics.get("low", 0) or 0)
    security_score = max(
        0, min(100, 100 - critical * 15 - high * 8 - medium * 4 - low * 2)
    )
    if security_score >= 90:
        return "Low"
    if security_score >= 75:
        return "Medium"
    if security_score >= 60:
        return "High"
    return "Critical"


def build_findings(
    gaps: list[GapAnalysis], frameworks: list[str]
) -> list[dict[str, Any]]:
    """Turn gap analyses into severity-ranked finding write-ups."""
    framework_label = ", ".join(frameworks) or "NIST Cyber Security Framework"
    findings: list[dict[str, Any]] = []
    for gap in sorted(gaps, key=lambda item: item.priority):
        severity = severity_for_priority(gap.priority)
        findings.append(
            {
                "finding_id": gap.analysis_id,
                "title": f"{gap.control_id} — {gap.gap_type}",
                "description": (
                    "Control "
                    f"{gap.control_id} ({gap.gap_type}) was not fully satisfied during "
                    f"the {framework_label} assessment."
                ),
                "severity": severity,
                "cvss_score": cvss_for_severity(severity),
                "affected_asset": gap.control_id,
                "remediation": gap.remediation,
                "compliance_framework": framework_label,
                "status": "Open",
                "discovered_at": datetime.now(),
            }
        )
    return findings


def build_statistics(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate severity counts plus average CVSS from the findings list."""
    counts: dict[str, Any] = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "informational": 0,
    }
    total_cvss = 0.0
    for finding in findings:
        severity = str(finding.get("severity", "")).lower()
        counts[severity] = counts.get(severity, 0) + 1
        try:
            total_cvss += float(finding.get("cvss_score", 0) or 0)
        except (TypeError, ValueError):
            continue
    counts["average_cvss"] = round(total_cvss / len(findings), 1) if findings else 0.0
    return counts


def build_recommendations(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prioritized remediation plan derived from finding severities."""
    recommendations: list[dict[str, Any]] = []
    for finding in findings:
        severity = str(finding.get("severity", "")).lower()
        template = RECOMMENDATION_TEMPLATES.get(severity)
        if template is None:
            continue
        title, description = template
        recommendations.append(
            {
                "priority": len(recommendations) + 1,
                "title": title,
                "description": description,
            }
        )
    return recommendations


def build_report_data(
    *,
    engagement: dict[str, Any],
    score: ResilienceScore | None,
    statuses: dict[str, str],
    controls: list[Control],
    verdicts: list[dict[str, Any]],
    gaps: list[GapAnalysis],
    report_id: str,
    generated_at: datetime,
) -> dict[str, Any]:
    """Assemble the full CYART-compatible report payload from M3 data."""
    del statuses, controls, verdicts

    organization = str(engagement.get("organization") or "Organization")
    framework_items = cast(
        "list[Any]", engagement.get("frameworks") or []
    )
    frameworks = [f"{item}" for item in framework_items]
    framework_label = ", ".join(frameworks) or "NIST Cyber Security Framework"

    findings = build_findings(gaps, frameworks)
    statistics = build_statistics(findings)

    band = score.band if score is not None else ""
    overall_risk = (
        BAND_RISK.get(band, "") or overall_risk_from_statistics(statistics)
    )

    total_findings = len(findings)
    critical = statistics.get("critical", 0)
    high = statistics.get("high", 0)
    medium = statistics.get("medium", 0)
    low = statistics.get("low", 0)
    average_cvss = statistics.get("average_cvss", 0.0)
    total_assets = 0

    if total_findings:
        summary_text = (
            "The assessment identified "
            f"{critical} Critical, {high} High, {medium} Medium and {low} "
            "Low severity findings "
            f"across {total_assets} assets. The average CVSS score is {average_cvss}. "
            f"The overall organizational risk is {overall_risk}."
        )
    else:
        summary_text = (
            "The assessment did not identify any actionable findings. The overall "
            "organizational risk is Low."
        )

    risk_matrix = {
        SEVERITY_TITLES[severity]: int(statistics.get(severity, 0) or 0)
        for severity in SEVERITY_TITLES
    }

    compliance_mapping = [
        {"framework": framework_label, "control": gap.control_id}
        for gap in sorted(gaps, key=lambda item: item.priority)
    ]

    return {
        "cover": {
            "report_id": report_id,
            "title": f"{organization} Security Assessment Report",
            "generated_at": generated_at,
        },
        "organization": {
            "name": organization,
            "industry": "",
            "website": "",
            "email": "",
            "phone": "",
            "country": "",
            "city": "",
            "address": "",
            "contact_person": "",
        },
        "scope": {
            "assessment_name": str(engagement.get("name") or "Security Assessment"),
            "assessment_type": "Security Assessment",
            "target": str(engagement.get("name") or "Assessment Target"),
            "assessment_period": generated_at.strftime("%B %Y"),
            "assessment_team": "M3 Offensive Security Team",
            "framework": framework_label,
            "testing_type": "Authenticated Assessment",
        },
        "methodology": {phase: True for phase in DEFAULT_METHODOLOGY_PHASES},
        "assets": [],
        "findings": findings,
        "statistics": statistics,
        "risk_matrix": risk_matrix,
        "recommendations": build_recommendations(findings),
        "appendix": {
            "tools": list(DEFAULT_TOOLS),
            "report_version": "1.0",
            "classification": "Confidential",
        },
        "references": list(DEFAULT_REFERENCES),
        "compliance_mapping": compliance_mapping,
        "footer": {
            "company": organization,
            "copyright": f"\u00a9 {generated_at.year} {organization}",
            "confidentiality": "CONFIDENTIAL",
        },
        "executive_summary": {
            "summary_text": summary_text,
            "overall_risk": overall_risk,
            "average_cvss": average_cvss,
            "total_assets": total_assets,
            "total_findings": total_findings,
            "severity_counts": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
                "informational": statistics.get("informational", 0),
            },
        },
        "dashboard": statistics,
    }