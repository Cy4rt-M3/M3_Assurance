"""
API layer for the Threat Intel Integration Pipeline (Task 1).

Exposes the enrichment pipeline over HTTP so other services (or you,
via the browser/Postman) can trigger lookups and retrieve stored data,
instead of running a Python script manually every time.

Run with:
    uvicorn api:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import ThreatIntel, get_session, init_db
from threat_intel_pipeline import enrich_and_save

app = FastAPI(title="Threat Intel Integration Pipeline")


class EnrichRequest(BaseModel):
    cve_ids: List[str]


class ThreatIntelRecord(BaseModel):
    cve_id: str
    cvss_score: Optional[float]
    severity: Optional[str]
    epss_score: Optional[float]
    epss_percentile: Optional[float]
    status: str
    error: Optional[str]

    class Config:
        from_attributes = True


@app.on_event("startup")
def on_startup():
    """Makes sure the database table exists before the app starts serving requests."""
    init_db()


@app.post("/api/v1/enrich-cves", response_model=List[ThreatIntelRecord])
def enrich_cves(request: EnrichRequest):
    """
    Fetches CVSS + EPSS for each CVE ID given, saves each result to the
    database, and returns them. Invalid IDs or failed lookups still
    come back in the response with status="error" rather than crashing
    the whole request.
    """
    if not request.cve_ids:
        raise HTTPException(status_code=400, detail="cve_ids list cannot be empty")

    results = enrich_and_save(request.cve_ids)
    return results


@app.get("/api/v1/threat-intel/{cve_id}", response_model=List[ThreatIntelRecord])
def get_threat_intel(cve_id: str):
    """
    Returns the stored enrichment result for a given CVE ID.
    Each CVE has exactly one row, always reflecting its most recent
    lookup (re-enriching a CVE updates its existing row rather than
    creating a duplicate).
    """
    session = get_session()
    try:
        rows = (
            session.query(ThreatIntel)
            .filter(ThreatIntel.cve_id == cve_id.strip().upper())
            .order_by(ThreatIntel.fetched_at.desc())
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"No data found for {cve_id}")
        return rows
    finally:
        session.close()


@app.get("/api/v1/threat-intel", response_model=List[ThreatIntelRecord])
def list_all_threat_intel():
    """Returns every stored enrichment result, most recent first."""
    session = get_session()
    try:
        rows = session.query(ThreatIntel).order_by(ThreatIntel.fetched_at.desc()).all()
        return rows
    finally:
        session.close()
