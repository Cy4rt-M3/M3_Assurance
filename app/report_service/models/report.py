
from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.report_service.models.organization import Organization
from app.report_service.models.Asset import Asset
from app.report_service.models.finding import Finding
from app.report_service.models.scope import Scope


class Report(BaseModel):
    report_id: str
    title: str

    organization: Organization

    scope: Scope

    assets: List[Asset]

    findings: List[Finding]

    generated_at: datetime