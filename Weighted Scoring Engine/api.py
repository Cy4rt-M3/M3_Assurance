"""
API layer for the Weighted Scoring Engine (Task 3).

Run with:
    python -m uvicorn api:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from database import RiskScore, get_session, init_db
from weighted_scoring_engine import (
    calculate_risk_score,
    save_result,
    fetch_cvss_epss,
    fetch_blast_radius,
)

app = FastAPI(title="Weighted Scoring Engine")


class DirectScoreInput(BaseModel):
    """Provide the three scores directly, if you already have them."""
    cve_id: str
    asset_id: str
    cvss_score: float = Field(..., ge=0, le=10)
    epss_score: float = Field(..., ge=0, le=1)
    blast_radius_score: float = Field(..., ge=0, le=100)


class LookupScoreInput(BaseModel):
    """Look up CVSS/EPSS and Blast Radius automatically from Task 1/2's databases."""
    cve_id: str
    asset_id: str


class RiskScoreRecord(BaseModel):
    cve_id: str
    asset_id: str
    cvss_score: float
    epss_score: float
    blast_radius_score: float
    composite_score: float
    risk_band: str

    class Config:
        from_attributes = True


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/api/v1/calculate-risk-score", response_model=RiskScoreRecord)
def calculate_risk_score_endpoint(input_data: DirectScoreInput):
    """
    Calculates and saves the final risk score using scores you provide directly.
    Re-submitting the same cve_id + asset_id pair updates the existing record.
    """
    try:
        result = calculate_risk_score(
            input_data.cvss_score, input_data.epss_score, input_data.blast_radius_score
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    save_result(input_data.cve_id, input_data.asset_id, result)
    return {"cve_id": input_data.cve_id, "asset_id": input_data.asset_id, **result}


@app.post("/api/v1/calculate-risk-score/lookup", response_model=RiskScoreRecord)
def calculate_risk_score_lookup_endpoint(input_data: LookupScoreInput):
    """
    Calculates and saves the final risk score by automatically looking up
    CVSS/EPSS (from Task 1's database) and Blast Radius (from Task 2's
    database). Both must have already been calculated for this CVE/asset.
    """
    cvss_score, epss_score = fetch_cvss_epss(input_data.cve_id)
    blast_radius_score = fetch_blast_radius(input_data.asset_id)

    missing = []
    if cvss_score is None:
        missing.append(f"CVSS/EPSS data for {input_data.cve_id}")
    if blast_radius_score is None:
        missing.append(f"Blast Radius data for {input_data.asset_id}")
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Missing required data: {', '.join(missing)}. "
                   f"Run Task 1/Task 2 for these first, or use /calculate-risk-score directly.",
        )

    result = calculate_risk_score(cvss_score, epss_score, blast_radius_score)
    save_result(input_data.cve_id, input_data.asset_id, result)
    return {"cve_id": input_data.cve_id, "asset_id": input_data.asset_id, **result}


@app.get("/api/v1/risk-score/{cve_id}/{asset_id}", response_model=RiskScoreRecord)
def get_risk_score(cve_id: str, asset_id: str):
    """Returns the stored final risk score for a specific CVE + asset pair."""
    session = get_session()
    try:
        row = (
            session.query(RiskScore)
            .filter(RiskScore.cve_id == cve_id.strip().upper(), RiskScore.asset_id == asset_id.strip())
            .first()
        )
        if not row:
            raise HTTPException(status_code=404, detail=f"No risk score found for {cve_id}/{asset_id}")
        return row
    finally:
        session.close()


@app.get("/api/v1/risk-scores", response_model=List[RiskScoreRecord])
def list_all_risk_scores():
    """Returns every stored risk score, highest risk first."""
    session = get_session()
    try:
        rows = session.query(RiskScore).order_by(RiskScore.composite_score.desc()).all()
        return rows
    finally:
        session.close()
