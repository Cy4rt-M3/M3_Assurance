from __future__ import annotations

import argparse
import logging
import sys

from pathlib import Path
from datetime import datetime, timezone
from typing import List

from app.report_service.report_engine import ReportEngine

from app.report_service.models.organization import Organization
from app.report_service.models.Asset import Asset
from app.report_service.models.finding import Finding
from app.report_service.models.scope import Scope
from app.report_service.models.report import Report

logger = logging.getLogger("cyart.report_generation")

# =====================================================
# SAMPLE DATA
# =====================================================
def build_sample_scope() -> Scope:

    return Scope(
        assessment_name="Internal Security Assessment",
        assessment_type="Web Application Penetration Test",
        target="CYART Production Infrastructure",
        assessment_period="July 2026",
        assessment_team="CYART Offensive Security Team",
        framework="NIST Cyber Security Framework",
        testing_type="Authenticated Assessment",
    )

def build_sample_assets() -> List[Asset]:

    now = datetime.now(timezone.utc)

    return [

        Asset(
            asset_id="AST-0001",
            hostname="WEB-PROD-01",
            ip_address="192.168.1.10",
            operating_system="Ubuntu 24.04",
            asset_type="Web Server",
            environment="Production",
            criticality="Critical",
            owner="Infrastructure Team",
            status="Active",
            last_scan=now,
        ),

        Asset(
            asset_id="AST-0002",
            hostname="DB-PROD-01",
            ip_address="192.168.1.20",
            operating_system="PostgreSQL 16",
            asset_type="Database Server",
            environment="Production",
            criticality="Critical",
            owner="Database Team",
            status="Active",
            last_scan=now,
        )

    ]
def build_sample_organization() -> Organization:

    return Organization(
        organization_id="ORG-0001",
        name="CYART",
        industry="Cybersecurity",
        website="https://cyart.io",
        email="security@cyart.io",
        phone="+91-9876543210",
        country="India",
        city="Mumbai",
        address="Mumbai, Maharashtra",
        contact_person="Security Team",
        created_at=datetime.now(timezone.utc),
    )
def build_sample_findings() -> List[Finding]:

    now = datetime.now(timezone.utc)

    return [

        Finding(
            finding_id="FND-0001",
            title="SQL Injection",
            description="SQL Injection vulnerability discovered in the login endpoint allowing attackers to manipulate database queries.",
            severity="Critical",
            cvss_score=9.8,
            affected_asset="WEB-PROD-01",
            remediation="Use parameterized queries and prepared statements.",
            compliance_framework="OWASP Top 10",
            status="Open",
            discovered_at=now,
        ),

        Finding(
            finding_id="FND-0002",
            title="Outdated Apache Server",
            description="Apache version is outdated and affected by publicly known vulnerabilities.",
            severity="High",
            cvss_score=8.4,
            affected_asset="WEB-PROD-01",
            remediation="Upgrade Apache to the latest supported version.",
            compliance_framework="NIST CSF",
            status="Open",
            discovered_at=now,
        ),

        Finding(
            finding_id="FND-0003",
            title="Weak TLS Configuration",
            description="TLS 1.0 is enabled on the production server.",
            severity="Medium",
            cvss_score=5.6,
            affected_asset="WEB-PROD-01",
            remediation="Disable TLS 1.0 and TLS 1.1.",
            compliance_framework="PCI DSS",
            status="Open",
            discovered_at=now,
        )

    ]


def build_sample_report(
    organization_name: str | None = None
) -> Report:

    organization = build_sample_organization()

    if organization_name:
        organization.name = organization_name

    return Report(

        report_id="RPT-0001",

        title=f"{organization.name} Internal Security Assessment Report",

        organization=organization,

        scope=build_sample_scope(),

        assets=build_sample_assets(),

        findings=build_sample_findings(),

        generated_at=datetime.now(timezone.utc),

    )

def parse_args():

    parser = argparse.ArgumentParser(

        description="Generate CYART Security Assessment Report"

    )

    parser.add_argument(

        "--output",

        type=Path,

        default=Path("tests/reports") / "cyart_report.pdf",

        help="Output PDF file"

    )

    parser.add_argument(

        "--organization-name",

        type=str,

        default=None,

        help="Override organization name"

    )

    parser.add_argument(

        "--log-level",

        default="INFO",

        choices=["DEBUG", "INFO", "WARNING", "ERROR"]

    )
    parser.add_argument(
        "--audience",
        type=str,
        default="technical",
        choices=[
            "executive",
            "ciso",
            "technical"
        ],
        help="Target audience for the report."
    )

    return parser.parse_args()

def configure_logging(level):

    logging.basicConfig(

        level=getattr(logging, level),

        format="%(asctime)s | %(levelname)s | %(message)s"

    )

# =====================================================
# MAIN
# =====================================================

def main() -> int:

    args = parse_args()

    configure_logging(args.log_level)

    logger.info("Building sample report...")

    report = build_sample_report(args.organization_name)

    output_path = args.output

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    logger.info("Generating PDF...")

    engine = ReportEngine(report)

    engine.generate_pdf(
        str(output_path)
    )

    logger.info("PDF Generated Successfully")

    print()

    print("=" * 60)
    print("PDF Generated Successfully")
    print(output_path.resolve())
    print("=" * 60)

    return 0

# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )

