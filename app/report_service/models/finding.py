from datetime import datetime
from pydantic import BaseModel


class Finding(BaseModel):
    finding_id: str
    title: str
    description: str
    severity: str
    cvss_score: float
    affected_asset: str
    remediation: str
    compliance_framework: str
    status: str
    discovered_at: datetime