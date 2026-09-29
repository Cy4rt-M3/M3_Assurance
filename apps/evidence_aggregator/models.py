"""Pydantic models for the Evidence Aggregator service."""

from pydantic import BaseModel, Field, field_validator

from apps.shared.ocsf import validate_events


class EvidenceLink(BaseModel):
    link_id: str
    control_id: str
    verdict_id: str
    evidence_hash: str
    chain_position: int = Field(..., ge=0)


class EvidenceSummary(BaseModel):
    engagement_id: str
    total_links: int
    unique_hashes: int
    completeness_pct: float


class IngestRequest(BaseModel):
    engagement_id: str
    name: str = "OCSF Engagement"
    organization: str = "CyArt Tech"
    frameworks: list[str] = Field(default_factory=list)
    events: list[dict[str, object]]

    @field_validator("events")
    @classmethod
    def check_events(cls, events: list[dict[str, object]]) -> list[dict[str, object]]:
        """Reject malformed OCSF events with a 422 before anything is stored."""
        return validate_events(events)


class IngestResponse(BaseModel):
    engagement_id: str
    ingested: int
    verdict_ids: list[str]
