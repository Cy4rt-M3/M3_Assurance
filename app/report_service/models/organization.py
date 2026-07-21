from pydantic import BaseModel, EmailStr
from datetime import datetime


class Organization(BaseModel):
    organization_id: str
    name: str
    industry: str
    website: str
    email: EmailStr
    phone: str
    country: str
    city: str
    address: str
    contact_person: str
    created_at: datetime