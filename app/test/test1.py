from datetime import datetime

from app.report_service.models.finding import Finding
from app.report_service.models.organization import Organization
from app.report_service.models.Asset import Asset
from app.report_service.models.scope import Scope
from app.report_service.models.report import Report

from app.report_service.builders.report_builder import ReportBuilder

organization = Organization(
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
    created_at=datetime.now()
)

scope = Scope(
    assessment_name="Internal Security Assessment",
    assessment_type="Web Application Penetration Test",
    target="CYART Production Infrastructure",
    assessment_period="July 2026",
    assessment_team="CYART Offensive Security Team",
    framework="NIST Cyber Security Framework",
    testing_type="Authenticated Assessment"
)

asset1 = Asset(
    asset_id="AST-0001",
    hostname="WEB-PROD-01",
    ip_address="192.168.1.10",
    operating_system="Ubuntu 24.04",
    asset_type="Web Server",
    environment="Production",
    criticality="Critical",
    owner="Infrastructure Team",
    status="Active",
    last_scan=datetime.now()
)

finding1 = Finding(
    finding_id="FND-0001",
    title="Outdated Apache Version",
    description="Apache server is running an unsupported version that may expose the server to known vulnerabilities.",
    severity="High",
    cvss_score=8.7,
    affected_asset="WEB-PROD-01",
    remediation="Upgrade Apache to the latest supported stable release.",
    compliance_framework="NIST CSF",
    status="Open",
    discovered_at=datetime.now()
)

report = Report(
    report_id="RPT-0001",
    title="CYART Internal Security Assessment Report",

    organization=organization,

    scope=scope,

    assets=[asset1],

    findings=[finding1],

    generated_at=datetime.now()
)
builder = ReportBuilder(report)

structured_report = builder.build()

print("========== ORGANIZATION ==========")
print(organization)

print("\n========== ASSET ==========")
print(asset1)

print("\n========== FINDING ==========")
print(finding1)

print("\n========== REPORT ==========")
print(report)

print("\n========== STRUCTURED REPORT ==========")
print(structured_report)

print("\n========== SCOPE ==========")
print(scope)