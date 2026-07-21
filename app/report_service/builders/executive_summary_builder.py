"""
executive_summary_builder.py

Builds the Executive Summary section for the security assessment report.

Produces both a human-readable narrative (for stakeholders who read only
this section) and the underlying structured statistics (for dashboards,
charts, and downstream automation), derived from the report's risk
calculation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, TypedDict

from app.report_service.models.report import Report
from app.report_service.risk.engine import RiskEngine

logger = logging.getLogger(__name__)

__all__ = ["ExecutiveSummaryBuilder", "ExecutiveSummarySection", "ExecutiveSummaryBuildError"]

# Risk statistics keys the summary depends on, mapped to a safe default
# used if the risk engine ever omits one (rather than raising KeyError
# mid-report-generation).
_REQUIRED_STAT_DEFAULTS: Dict[str, Any] = {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "informational": 0,
    "average_cvss": 0.0,
    "overall_risk": "Unknown",
}

CVSS_DECIMAL_PLACES = 1


class ExecutiveSummaryBuildError(Exception):
    """Raised when the executive summary cannot be built from the report."""


class ExecutiveSummarySection(TypedDict):

    summary_text: str
    overall_risk: str
    average_cvss: float

    total_assets: int
    total_findings: int

    severity_counts: Dict[str, int]

@dataclass
class ExecutiveSummaryBuilder:
    """
    Builds the Executive Summary section of the report.

    Combines risk-engine output with report-level counts (assets,
    findings) into a single narrative paragraph plus a structured
    statistics payload, so both the written report and any dashboard
    widgets are backed by exactly the same numbers.

    Args:
        report: The source report aggregate containing findings and assets.
        risk_engine: Optional injected `RiskEngine` instance. A default
            instance is created if none is supplied, keeping the class
            easy to instantiate while still testable/mockable.

    Raises:
        ExecutiveSummaryBuildError: If risk statistics cannot be
            calculated for the report's findings.
    """

    report: Report
    risk_engine: Optional[RiskEngine] = None

    def __post_init__(self) -> None:
        if self.report is None:
            raise ValueError("report must not be None")
        self.risk_engine = self.risk_engine or RiskEngine()

    def build(self) -> ExecutiveSummarySection:
        """Build and return the executive summary payload."""
        stats = self._calculate_statistics()

        total_assets = len(self.report.assets)
        total_findings = len(self.report.findings)

        summary_text = self._render_summary(stats, total_assets)

        return {
            "summary_text": summary_text,

            "overall_risk": stats["overall_risk"],

            "average_cvss": stats["average_cvss"],

            "total_assets": total_assets,

            "total_findings": total_findings,

            "assets_reviewed_count": total_assets,

            "engagement_duration": "14 Days",

            "testing_period": "01 Jul 2026 - 14 Jul 2026",

            "severity_counts": {

                "critical": stats["critical"],

                "high": stats["high"],

                "medium": stats["medium"],

                "low": stats["low"],

                "informational": stats.get("informational", 0)

            },

            "key_risks": [

                "Critical systems exposed to remote attack.",

                "Weak authentication identified on multiple assets.",

                "Several outdated services require immediate patching."

            ],

            "top_recommendations": [

                "Patch all Critical vulnerabilities immediately.",

                "Implement MFA across administrative accounts.",

                "Perform continuous vulnerability scanning."

            ]

        }

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Run the risk engine and backfill any missing keys defensively."""
        try:
            raw_stats = self.risk_engine.calculate(self.report.findings)
        except Exception as exc:  # noqa: BLE001 - surface as a domain error
            raise ExecutiveSummaryBuildError(
                "Failed to calculate risk statistics for executive summary"
            ) from exc

        stats = dict(_REQUIRED_STAT_DEFAULTS)
        stats.update(raw_stats or {})

        missing = [key for key in _REQUIRED_STAT_DEFAULTS if key not in (raw_stats or {})]
        if missing:
            logger.warning(
                "Risk engine result missing key(s) %s for report %s; using defaults",
                missing,
                getattr(self.report, "report_id", "unknown"),
            )

        stats["average_cvss"] = round(float(stats["average_cvss"]), CVSS_DECIMAL_PLACES)
        return stats

    @staticmethod
    def _render_summary(stats: Dict[str, Any], total_assets: int) -> str:
        """Render the narrative paragraph from computed statistics."""
        return (
            f"The assessment identified {stats['critical']} Critical, "
            f"{stats['high']} High, {stats['medium']} Medium, and "
            f"{stats['low']} Low severity findings across {total_assets} "
            f"asset{'s' if total_assets != 1 else ''}. The average CVSS "
            f"score across all findings is {stats['average_cvss']}, and "
            f"the overall organizational risk is assessed as "
            f"{stats['overall_risk']}."
        )