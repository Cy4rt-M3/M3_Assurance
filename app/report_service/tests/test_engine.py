"""
generate_report.py

Command-line entry point for generating a CYART security assessment report.

This script is intentionally kept free of "hardcoded demo" smells:
  * Sample/seed data lives in its own factory functions (`sample_data.py`
    style, inlined here for a single-file deliverable) so it's obvious
    what's fixture data vs. what's real report-generation logic.
  * All I/O (output path, log level, organization name) is CLI-configurable
    instead of buried in the script body.
  * Failures are caught, logged with context, and produce a non-zero exit
    code — so this is safe to run in CI/automation, not just interactively.

Usage:
    python generate_report.py
    python generate_report.py --output reports/cyart_q3.pdf --log-level DEBUG
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.report_service.report_engine import ReportEngine
from app.report_service.models.organization import Organization
from app.report_service.models.Asset import Asset
from app.report_service.models.finding import Finding
from app.report_service.models.scope import Scope
from app.report_service.models.report import Report

logger = logging.getLogger("cyart.report_generation")


# =====================================================
# SAMPLE / SEED DATA FACTORIES
# =====================================================
# These build a realistic, MNC-scale assessment: multiple assets across
# environments, and findings spanning the full severity spectrum with
# distinct compliance frameworks — the shape a real pentest report has,
# rather than a single toy finding.

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
            operating_system="PostgreSQL 16 / Debian 12",
            asset_type="Database Server",
            environment="Production",
            criticality="Critical",
            owner="Data Platform Team",
            status="Active",
            last_scan=now,
        ),
        Asset(
            asset_id="AST-0003",
            hostname="API-GW-01",
            ip_address="192.168.1.30",
            operating_system="Amazon Linux 2023",
            asset_type="API Gateway",
            environment="Production",
            criticality="High",
            owner="Platform Engineering",
            status="Active",
            last_scan=now,
        ),
        Asset(
            asset_id="AST-0004",
            hostname="LB-PROD-01",
            ip_address="192.168.1.40",
            operating_system="F5 BIG-IP 17.x",
            asset_type="Load Balancer",
            environment="Production",
            criticality="Medium",
            owner="Network Team",
            status="Active",
            last_scan=now,
        ),
    ]


def build_sample_findings() -> List[Finding]:
    now = datetime.now(timezone.utc)
    return [
        Finding(
            finding_id="FND-0001",
            title="SQL Injection in Authentication Endpoint",
            description=(
                "The /api/v1/login endpoint fails to sanitize the "
                "'username' parameter, allowing an attacker to bypass "
                "authentication and extract arbitrary database records "
                "via boolean- and time-based blind SQL injection."
            ),
            severity="Critical",
            cvss_score=9.8,
            affected_asset="WEB-PROD-01",
            remediation=(
                "Use parameterized queries / prepared statements for all "
                "database access. Deploy a WAF rule as an interim "
                "compensating control and rotate any credentials that may "
                "have been exposed."
            ),
            compliance_framework="OWASP Top 10 (A03:2021 - Injection)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0002",
            title="Outdated Apache HTTP Server Version",
            description=(
                "WEB-PROD-01 is running Apache 2.4.49, which is affected "
                "by publicly known path traversal and remote code "
                "execution vulnerabilities (CVE-2021-41773, "
                "CVE-2021-42013)."
            ),
            severity="High",
            cvss_score=8.7,
            affected_asset="WEB-PROD-01",
            remediation=(
                "Upgrade Apache HTTP Server to the latest supported stable "
                "release and enable automated patch management for "
                "internet-facing hosts."
            ),
            compliance_framework="NIST CSF (PR.IP-12)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0003",
            title="Excessive Database Privileges for Application User",
            description=(
                "The application's database service account has "
                "superuser privileges on DB-PROD-01, violating the "
                "principle of least privilege and increasing blast radius "
                "in the event of application compromise."
            ),
            severity="High",
            cvss_score=7.8,
            affected_asset="DB-PROD-01",
            remediation=(
                "Create a dedicated least-privilege role scoped to only "
                "the schemas and operations the application requires; "
                "revoke superuser access."
            ),
            compliance_framework="ISO 27001 (A.9.2.3)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0004",
            title="Weak TLS Configuration",
            description=(
                "LB-PROD-01 accepts TLS 1.0 and TLS 1.1 connections and "
                "supports several weak cipher suites (e.g. RC4, 3DES)."
            ),
            severity="Medium",
            cvss_score=5.6,
            affected_asset="LB-PROD-01",
            remediation=(
                "Disable TLS 1.0/1.1 and weak cipher suites; enforce "
                "TLS 1.2+ with modern cipher preference ordering."
            ),
            compliance_framework="PCI-DSS (Req. 4.1)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0005",
            title="Missing Rate Limiting on API Gateway",
            description=(
                "API-GW-01 does not enforce per-client rate limiting on "
                "authentication and password-reset endpoints, enabling "
                "credential-stuffing and brute-force attacks."
            ),
            severity="Medium",
            cvss_score=5.3,
            affected_asset="API-GW-01",
            remediation=(
                "Implement per-IP and per-account rate limiting with "
                "exponential backoff and CAPTCHA challenges on "
                "authentication endpoints."
            ),
            compliance_framework="OWASP API Security Top 10 (API4:2023)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0006",
            title="Verbose Server Banner Disclosure",
            description=(
                "HTTP response headers on WEB-PROD-01 disclose exact "
                "server software and version, aiding attacker "
                "reconnaissance."
            ),
            severity="Low",
            cvss_score=3.1,
            affected_asset="WEB-PROD-01",
            remediation="Suppress or generalize Server/X-Powered-By headers.",
            compliance_framework="NIST CSF (PR.PT-1)",
            status="Open",
            discovered_at=now,
        ),
        Finding(
            finding_id="FND-0007",
            title="Missing Security Headers",
            description=(
                "Responses from WEB-PROD-01 lack Content-Security-Policy, "
                "X-Frame-Options, and X-Content-Type-Options headers."
            ),
            severity="Informational",
            cvss_score=0.0,
            affected_asset="WEB-PROD-01",
            remediation=(
                "Add standard hardening headers at the load balancer or "
                "application layer."
            ),
            compliance_framework="OWASP Secure Headers Project",
            status="Open",
            discovered_at=now,
        ),
    ]


def build_sample_report(organization_name: str | None = None) -> Report:
    """Assemble a full sample `Report` domain object.

    Args:
        organization_name: Optional override for the organization name,
            useful for generating white-labeled sample reports without
            editing this file.
    """
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


# =====================================================
# CLI
# =====================================================

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a CYART security assessment PDF report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / f"cyart_report_{datetime.now():%Y%m%d_%H%M%S}.pdf",
        help="Path to write the generated PDF report to "
             "(default: reports/cyart_report_<timestamp>.pdf).",
    )
    parser.add_argument(
        "--organization-name",
        type=str,
        default=None,
        help="Override the organization name used in the sample report.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO).",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =====================================================
# ENTRY POINT
# =====================================================

def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.log_level)

    logger.info("Building sample assessment report data")
    try:
        report = build_sample_report(organization_name=args.organization_name)
    except Exception:
        logger.exception("Failed to construct report domain objects")
        return 1

    logger.info(
        "Report '%s' assembled: %d assets, %d findings",
        report.report_id,
        len(report.assets),
        len(report.findings),
    )

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Generating PDF report -> %s", output_path)
    try:
        engine = ReportEngine(report)
        engine.generate_pdf(str(output_path))
    except Exception:
        logger.exception("PDF generation failed")
        return 1

    if not output_path.exists():
        logger.error("Engine reported success but output file is missing: %s", output_path)
        return 1

    size_kb = output_path.stat().st_size / 1024
    logger.info(
        "PDF generated successfully: %s (%.1f KB)",
        output_path.resolve(),
        size_kb,
    )
    print(f"PDF Generated Successfully: {output_path.resolve()} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())