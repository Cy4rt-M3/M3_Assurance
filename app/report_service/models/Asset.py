from datetime import datetime
from pydantic import BaseModel


class Asset(BaseModel):
    asset_id: str
    hostname: str
    ip_address: str
    operating_system: str
    asset_type: str
    environment: str
    criticality: str
    owner: str
    status: str
    last_scan: datetime