from datetime import datetime

from app.report_service.models.finding import Finding
from app.report_service.risk.engine import RiskEngine

findings = [

    Finding(
        finding_id="1",
        title="SQL Injection",
        description="",
        severity="Critical",
        cvss_score=9.8,
        affected_asset="Server",
        remediation="Patch",
        compliance_framework="OWASP",
        status="Open",
        discovered_at=datetime.now()
    ),

    Finding(
        finding_id="2",
        title="Weak TLS",
        description="",
        severity="Medium",
        cvss_score=5.5,
        affected_asset="Server",
        remediation="Disable TLS 1.0",
        compliance_framework="NIST",
        status="Open",
        discovered_at=datetime.now()
    ),

    Finding(
        finding_id="3",
        title="Apache Version",
        description="",
        severity="High",
        cvss_score=8.2,
        affected_asset="Server",
        remediation="Upgrade Apache",
        compliance_framework="NIST",
        status="Open",
        discovered_at=datetime.now()
    )

]

engine = RiskEngine()

risk = engine.calculate(findings)

print(risk)