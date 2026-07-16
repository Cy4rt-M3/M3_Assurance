"""
API layer for the Blast Radius Engine (Task 2).

Run with:
    python -m uvicorn api:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from database import BlastRadiusScore, get_session, init_db
from blast_radius_engine import (
    calculate_blast_radius,
    save_result,
    EXPOSURE_SCORES,
    CRITICALITY_SCORES,
)

app = FastAPI(title="Blast Radius Engine")


class AssetInput(BaseModel):
    asset_id: str
    exposure_level: str = Field(
        ..., description=f"One of: {list(EXPOSURE_SCORES.keys())}"
    )
    criticality: str = Field(
        ..., description=f"One of: {list(CRITICALITY_SCORES.keys())}"
    )
    connected_assets_count: int = Field(..., ge=0)


class BlastRadiusRecord(BaseModel):
    asset_id: str
    exposure_level: str
    criticality: str
    connected_assets_count: int
    exposure_score: float
    criticality_score: float
    connectivity_score: float
    blast_radius_score: float

    class Config:
        from_attributes = True


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/api/v1/calculate-blast-radius", response_model=BlastRadiusRecord)
def calculate_blast_radius_endpoint(asset: AssetInput):
    """
    Calculates the Blast Radius score for one asset and saves it.
    Re-submitting the same asset_id updates its existing record rather
    than creating a duplicate.
    """
    try:
        result = calculate_blast_radius(
            asset.asset_id,
            asset.exposure_level,
            asset.criticality,
            asset.connected_assets_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    save_result(result)
    return result


@app.get("/api/v1/blast-radius/{asset_id}", response_model=BlastRadiusRecord)
def get_blast_radius(asset_id: str):
    """Returns the stored Blast Radius score for one asset."""
    session = get_session()
    try:
        row = (
            session.query(BlastRadiusScore)
            .filter(BlastRadiusScore.asset_id == asset_id.strip())
            .first()
        )
        if not row:
            raise HTTPException(
                status_code=404, detail=f"No data found for asset '{asset_id}'"
            )
        return row
    finally:
        session.close()


@app.get("/api/v1/blast-radius", response_model=List[BlastRadiusRecord])
def list_all_blast_radius():
    """Returns every asset's stored Blast Radius score, highest risk first."""
    session = get_session()
    try:
        rows = (
            session.query(BlastRadiusScore)
            .order_by(BlastRadiusScore.blast_radius_score.desc())
            .all()
        )
        return rows
    finally:
        session.close()
