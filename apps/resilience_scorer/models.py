"""Pydantic models for the Resilience Scorer service."""

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    engagement_id: str
    framework_ids: list[str]


class ResilienceScore(BaseModel):
    score_id: str
    engagement_id: str
    composite_score: float = Field(..., ge=0.0, le=100.0)
    coverage_score: float = Field(..., ge=0.0, le=100.0)
    detection_score: float = Field(..., ge=0.0, le=100.0)
    evidence_score: float = Field(..., ge=0.0, le=100.0)
    band: str = Field(
        ..., description="Critical | At Risk | Moderate | Strong | Resilient"
    )


class ThreatIntelRequest(BaseModel):
    """Request for fetching threat intelligence."""

    cve_id: str


class ThreatIntelResponse(BaseModel):
    """Threat intelligence fetched from external APIs."""

    cve_id: str
    cvss_score: float = Field(..., ge=0.0, le=10.0)
    epss_score: float = Field(..., ge=0.0, le=1.0)


class BlastRadiusRequest(BaseModel):
    """Asset information used to calculate blast radius."""

    asset_id: str
    internet_facing: bool
    production: bool
    sensitive_data: bool
    user_count: int = Field(..., ge=0)


class BlastRadiusResponse(BaseModel):
    """Calculated blast radius."""

    asset_id: str
    blast_radius_score: float = Field(..., ge=0.0, le=100.0)


class WeightedRiskResponse(BaseModel):
    """Final weighted risk score."""

    cvss_score: float = Field(..., ge=0.0, le=10.0)
    epss_score: float = Field(..., ge=0.0, le=1.0)
    blast_radius_score: float = Field(..., ge=0.0, le=100.0)
    final_score: float = Field(..., ge=0.0, le=100.0)
    band: str
