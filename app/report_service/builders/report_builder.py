"""
report_builder.py

Builds the full, structured security assessment report payload from a
`Report` domain object. Each `build_*` method returns a JSON-serializable
section; `build()` assembles all sections into the final report document.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import Any, Dict, List, Optional, TypedDict
from app.report_service.statistics.engine import StatisticsEngine

from app.report_service.builders.dashboard_builder import DashboardBuilder
from app.report_service.builders.executive_summary_builder import ExecutiveSummaryBuilder
from app.report_service.builders.cover_builder import CoverBuilder
from app.report_service.models.report import Report
from app.report_service.recommendation.engine import RecommendationEngine
from app.report_service.risk.engine import RiskEngine

logger = logging.getLogger(__name__)


# =====================================================
# EXCEPTIONS
# =====================================================

class ReportBuildError(Exception):
    """Raised when a report section cannot be built."""


# =====================================================
# ENUMS / CONSTANTS
# =====================================================

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"

    @classmethod
    def from_raw(cls, raw: str | None) -> "Severity":
        """Normalize an arbitrary severity string into a known Severity.

        Falls back to INFORMATIONAL for unknown/missing values rather than
        raising, since severity classification should never abort a report.
        """
        if not raw:
            return cls.INFORMATIONAL
        try:
            return cls(raw.strip().lower())
        except ValueError:
            logger.warning("Unrecognized severity %r; defaulting to Informational", raw)
            return cls.INFORMATIONAL


@dataclass(frozen=True)
class ReportConfig:
    """Static/report-wide configuration, overridable per report instance."""

    assessment_name: str = "Internal Security Assessment"
    assessment_type: str = "Web Application Security Assessment"
    target: str = "CYART Internal Infrastructure"
    assessment_period: str = "July 2026"
    assessment_team: str = "CYART Offensive Security Team"
    framework: str = "NIST Cyber Security Framework"
    testing_type: str = "Authenticated Assessment"

    tools_used: List[str] = field(default_factory=lambda: [
        "Nmap",
        "Nessus",
        "Burp Suite Professional",
        "OWASP ZAP",
    ])
    references: List[str] = field(default_factory=lambda: [
        "OWASP Top 10",
        "NIST Cyber Security Framework",
        "MITRE ATT&CK",
        "CIS Controls",
    ])

    report_version: str = "1.0"
    classification: str = "Confidential"

    company_name: str = "CYART"
    copyright_notice: str = "\u00a9 2026 CYART"
    confidentiality_notice: str = "CONFIDENTIAL"


DEFAULT_METHODOLOGY_PHASES: List[str] = [
    "Planning",
    "Reconnaissance",
    "Vulnerability Assessment",
    "Manual Validation",
    "Risk Analysis",
    "Reporting",
]

DEFAULT_COMPLIANCE_MAPPING: List[Dict[str, str]] = [
    {"framework": "NIST CSF", "control": "PR.IP-12"},
    {"framework": "ISO 27001", "control": "A.12.6"},
]

DEFAULT_RECOMMENDATIONS: List[Dict[str, Any]] = [
    {
        "priority": 1,
        "title": "Patch Critical Servers",
        "description": "Upgrade all production Apache servers.",
    },
    {
        "priority": 2,
        "title": "Implement Continuous Vulnerability Scanning",
        "description": "Perform weekly authenticated scans.",
    },
    {
        "priority": 3,
        "title": "Security Awareness Training",
        "description": "Conduct quarterly security awareness sessions.",
    },
]

DATE_FORMAT = "%Y-%m-%d %H:%M %Z"


# =====================================================
# TYPE DEFINITIONS (for editor/type-checker support)
# =====================================================

class CoverSection(TypedDict):
    report_id: str
    title: str
    organization: str
    generated_at: str


class ExecutiveSummarySection(TypedDict):
    summary_text: str
    overall_risk: str


# =====================================================
# REPORT BUILDER
# =====================================================

class ReportBuilder:
    """Builds a full, structured report payload from a `Report` domain object.

    Each `build_*` method returns a JSON-serializable section. `build()`
    assembles all sections into the final report document.
    """

    def __init__(
            self,
            report: Report,
            audience=None,
            risk_engine=None,
            recommendation_engine=None,
            config=None,
    ):

        if report is None:
            raise ValueError("report must not be None")

        # Save report
        self.report = report

        # Audience (Executive / Technical / Board)
        self.audience = audience

        # Configuration
        self.config = config or ReportConfig()

        # Engines
        self.risk_engine = risk_engine or RiskEngine()
        self.statistics_engine = StatisticsEngine(report)
        self.dashboard_builder = DashboardBuilder(report)

        # Builders
        self.cover_builder = CoverBuilder(report)
        self.executive_builder = ExecutiveSummaryBuilder(report)

        # Recommendation Engine
        self._recommendation_engine = recommendation_engine

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def _format_timestamp(value: Any) -> str:
        """Normalize a datetime (or datetime-like value) to a display string."""
        if isinstance(value, datetime):
            return value.strftime(DATE_FORMAT).strip()
        if value:
            return str(value)
        logger.warning("Report generated_at missing; using current UTC time.")
        return datetime.utcnow().strftime(DATE_FORMAT).strip()

    @staticmethod
    def _safe_str(value: Any) -> Optional[str]:
        """Coerce optional fields to str, preserving None instead of stringifying it."""
        return str(value) if value is not None else None

    # =====================================================
    # COVER
    # =====================================================

    def build_cover(self):

        """
        Delegates Cover creation to CoverBuilder.

        ReportBuilder should not know
        how the Cover is constructed.
        """

        return self.cover_builder.build()

    # =====================================================
    # DASHBOARD
    # =====================================================

    def build_dashboard(self) -> Dict[str, Any]:
        return self.dashboard_builder.build()

    # =====================================================
    # ORGANIZATION
    # =====================================================

    def build_organization(self) -> Dict[str, Any]:
        org = self.report.organization

        return {
            "name": org.name,
            "industry": self._safe_str(org.industry),
            "website": self._safe_str(org.website),
            "email": self._safe_str(org.email),
            "phone": self._safe_str(org.phone),
            "country": self._safe_str(org.country),
            "city": self._safe_str(org.city),
            "address": self._safe_str(org.address),
            "contact_person": self._safe_str(org.contact_person),
        }

    # =====================================================
    # ASSETS
    # =====================================================

    def build_assets(self) -> List[Dict[str, Any]]:
        return [
            {
                "asset_id": asset.asset_id,
                "hostname": asset.hostname,
                "ip_address": asset.ip_address,
                "operating_system": asset.operating_system,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "criticality": asset.criticality,
                "owner": asset.owner,
                "status": asset.status,
                "last_scan": asset.last_scan,
            }
            for asset in self.report.assets
        ]

    # =====================================================
    # FINDINGS
    # =====================================================

    def build_findings(self) -> List[Dict[str, Any]]:
        return [
            {
                "finding_id": finding.finding_id,
                "title": finding.title,
                "description": finding.description,
                "severity": finding.severity,
                "cvss_score": finding.cvss_score,
                "affected_asset": finding.affected_asset,
                "remediation": finding.remediation,
                "compliance_framework": finding.compliance_framework,
                "status": finding.status,
                "discovered_at": finding.discovered_at,
            }
            for finding in self.report.findings
        ]

    # =====================================================
    # STATISTICS
    # =====================================================

    def build_statistics(self) -> Dict[str, Any]:
        """
        Build the statistics section for the report.

        This delegates all calculations to the StatisticsEngine.

        """

        return self.statistics_engine.generate()

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================

    def build_executive_summary(self):

        return self.executive_builder.build()

    # =====================================================
    # SCOPE
    # =====================================================

    def build_scope(self) -> Dict[str, str]:
        cfg = self.config
        return {
            "assessment_name": cfg.assessment_name,
            "assessment_type": cfg.assessment_type,
            "target": cfg.target,
            "assessment_period": cfg.assessment_period,
            "assessment_team": cfg.assessment_team,
            "framework": cfg.framework,
            "testing_type": cfg.testing_type,
        }

    # =====================================================
    # METHODOLOGY
    # =====================================================

    def build_methodology(self) -> Dict[str, bool]:
        return {phase: True for phase in DEFAULT_METHODOLOGY_PHASES}

    # =====================================================
    # RISK MATRIX
    # =====================================================

    def build_risk_matrix(self) -> Dict[str, int]:
        matrix: Dict[str, int] = {severity.name.title(): 0 for severity in Severity}

        for finding in self.report.findings:
            severity = Severity.from_raw(getattr(finding, "severity", None))
            matrix[severity.name.title()] += 1

        return matrix

    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    def build_recommendations(self) -> List[Dict[str, Any]]:
        try:
            engine = self._get_recommendation_engine()
            generated = engine.generate()
            if generated:
                return generated
        except AttributeError:
            # Engine has no `generate` method wired up yet; fall back below.
            logger.debug("RecommendationEngine.generate unavailable; using defaults")
        except Exception:
            logger.exception("Recommendation engine failed; using default recommendations")

        return list(DEFAULT_RECOMMENDATIONS)

    # =====================================================
    # APPENDIX
    # =====================================================

    def build_appendix(self) -> Dict[str, Any]:
        return {
            "tools": list(self.config.tools_used),
            "report_version": self.config.report_version,
            "classification": self.config.classification,
        }

    # =====================================================
    # REFERENCES
    # =====================================================

    def build_references(self) -> List[str]:
        return list(self.config.references)

    # =====================================================
    # COMPLIANCE
    # =====================================================

    def build_compliance_mapping(self) -> List[Dict[str, str]]:
        return list(DEFAULT_COMPLIANCE_MAPPING)

    # =====================================================
    # FOOTER
    # =====================================================

    def build_footer(self) -> Dict[str, str]:
        return {
            "company": self.config.company_name,
            "copyright": self.config.copyright_notice,
            "confidentiality": self.config.confidentiality_notice,
        }

    # =====================================================
    # BUILD COMPLETE REPORT
    # =====================================================

    def build(self) -> Dict[str, Any]:
        """Assemble the full report. Raises ReportBuildError if any
        section fails, with the failing section name for easier debugging."""

        sections = (
            ("cover", self.build_cover),
            ("dashboard", self.build_dashboard),
            ("executive_summary", self.build_executive_summary),
            ("organization", self.build_organization),
            ("scope", self.build_scope),
            ("methodology", self.build_methodology),
            ("assets", self.build_assets),
            ("findings", self.build_findings),
            ("statistics", self.build_statistics),
            ("risk_matrix", self.build_risk_matrix),
            ("recommendations", self.build_recommendations),
            ("appendix", self.build_appendix),
            ("references", self.build_references),
            ("compliance_mapping", self.build_compliance_mapping),
            ("footer", self.build_footer),
        )

        report_data: Dict[str, Any] = {}

        allowed = None

        if self.audience is not None:
            allowed = set(self.audience.allowed_sections())
        for name, builder_fn in sections:
            try:
                report_data[name] = builder_fn()
            except ReportBuildError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed building report section %r", name)
                raise ReportBuildError(f"Failed building section '{name}'") from exc

        logger.info(
            "Report %s built successfully (%d assets, %d findings)",
            getattr(self.report, "report_id", "unknown"),
            len(self.report.assets),
            len(self.report.findings),
        )
        return report_data

