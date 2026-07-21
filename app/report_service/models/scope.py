from pydantic import BaseModel


class Scope(BaseModel):
    assessment_name: str
    assessment_type: str
    target: str
    assessment_period: str
    assessment_team: str
    framework: str
    testing_type: str