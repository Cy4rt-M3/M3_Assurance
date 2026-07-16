"""
Weighted Scoring Engine (Task 3) - core logic.

Combines three inputs into one final 0-100 risk score for a specific
CVE affecting a specific asset:

  - CVSS score          (0-10)   - how severe the vulnerability is
  - EPSS score          (0-1)    - how likely it is to be exploited
  - Blast Radius score  (0-100)  - how much damage spreads if compromised

ASSUMPTION (task description didn't give exact weights - flag this to
your team lead to confirm, same as the Blast Radius weights):
  - CVSS         : 40% weight
  - EPSS         : 35% weight
  - Blast Radius : 25% weight
This mirrors the same 40/35/25 pattern used elsewhere in the project
for consistency. The risk bands (Low/Medium/High/Critical) are also
an assumption, not stated in the task - adjust freely.

This engine can get its CVSS/EPSS/Blast Radius inputs two ways:
  1. Directly, as numbers you already have.
  2. Automatically, by looking them up from Task 1's and Task 2's
     databases (threat_intel.db, blast_radius.db), if those files
     are accessible.
"""

import sqlite3
import logging

from database import RiskScore, get_session, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("weighted_scoring_engine")

CVSS_WEIGHT = 0.40
EPSS_WEIGHT = 0.35
BLAST_RADIUS_WEIGHT = 0.25

RISK_BANDS = [
    (85, "Critical"),
    (65, "High"),
    (40, "Medium"),
    (0, "Low"),
]


def classify_risk_band(score: float) -> str:
    """Converts a 0-100 score into a Low/Medium/High/Critical label."""
    for threshold, label in RISK_BANDS:
        if score >= threshold:
            return label
    return "Low"  # fallback, shouldn't normally be reached


def calculate_risk_score(cvss_score: float, epss_score: float, blast_radius_score: float) -> dict:
    """
    Combines CVSS (0-10), EPSS (0-1), and Blast Radius (0-100) into one
    final 0-100 risk score. CVSS and EPSS are scaled up to 0-100 first
    so all three components are on the same scale before weighting.
    """
    if not (0 <= cvss_score <= 10):
        raise ValueError(f"cvss_score must be between 0 and 10, got {cvss_score}")
    if not (0 <= epss_score <= 1):
        raise ValueError(f"epss_score must be between 0 and 1, got {epss_score}")
    if not (0 <= blast_radius_score <= 100):
        raise ValueError(f"blast_radius_score must be between 0 and 100, got {blast_radius_score}")

    cvss_normalized = cvss_score * 10        # 0-10  -> 0-100
    epss_normalized = epss_score * 100       # 0-1   -> 0-100
    # blast_radius_score is already 0-100

    composite_score = (
        (cvss_normalized * CVSS_WEIGHT)
        + (epss_normalized * EPSS_WEIGHT)
        + (blast_radius_score * BLAST_RADIUS_WEIGHT)
    )
    composite_score = round(composite_score, 2)

    return {
        "cvss_score": cvss_score,
        "epss_score": epss_score,
        "blast_radius_score": blast_radius_score,
        "cvss_normalized": round(cvss_normalized, 2),
        "epss_normalized": round(epss_normalized, 2),
        "composite_score": composite_score,
        "risk_band": classify_risk_band(composite_score),
    }


def fetch_cvss_epss(cve_id: str, threat_intel_db_path: str = "../task1_threat_intel/threat_intel.db"):
    """
    Looks up the stored CVSS/EPSS data for a CVE from Task 1's database.
    Returns (cvss_score, epss_score) or (None, None) if not found.
    Uses plain sqlite3 (not SQLAlchemy) so this file doesn't depend on
    Task 1's code being importable - just its database file being reachable.
    """
    try:
        conn = sqlite3.connect(threat_intel_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cvss_score, epss_score FROM threat_intel WHERE cve_id = ? "
            "ORDER BY fetched_at DESC LIMIT 1",
            (cve_id.strip().upper(),),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None, None
        return row[0], row[1]
    except sqlite3.Error as exc:
        logger.error("Could not read threat_intel.db at %s: %s", threat_intel_db_path, exc)
        return None, None


def fetch_blast_radius(asset_id: str, blast_radius_db_path: str = "../task2_blast_radius/blast_radius.db"):
    """
    Looks up the stored Blast Radius score for an asset from Task 2's database.
    Returns the score, or None if not found.
    """
    try:
        conn = sqlite3.connect(blast_radius_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT blast_radius_score FROM blast_radius_scores WHERE asset_id = ?",
            (asset_id.strip(),),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return row[0]
    except sqlite3.Error as exc:
        logger.error("Could not read blast_radius.db at %s: %s", blast_radius_db_path, exc)
        return None


def save_result(cve_id: str, asset_id: str, result: dict, db_path: str = "risk_scores.db") -> None:
    """
    Saves the final risk score for a (cve_id, asset_id) pair.
    Re-scoring the same pair UPDATES the existing row instead of
    creating a duplicate.
    """
    session = get_session(db_path)
    try:
        existing = (
            session.query(RiskScore)
            .filter(RiskScore.cve_id == cve_id, RiskScore.asset_id == asset_id)
            .first()
        )

        if existing:
            existing.cvss_score = result["cvss_score"]
            existing.epss_score = result["epss_score"]
            existing.blast_radius_score = result["blast_radius_score"]
            existing.composite_score = result["composite_score"]
            existing.risk_band = result["risk_band"]
        else:
            row = RiskScore(
                cve_id=cve_id,
                asset_id=asset_id,
                cvss_score=result["cvss_score"],
                epss_score=result["epss_score"],
                blast_radius_score=result["blast_radius_score"],
                composite_score=result["composite_score"],
                risk_band=result["risk_band"],
            )
            session.add(row)

        session.commit()
    finally:
        session.close()


def score_and_save(
    cve_id: str,
    asset_id: str,
    cvss_score: float,
    epss_score: float,
    blast_radius_score: float,
    db_path: str = "risk_scores.db",
) -> dict:
    """Calculates and saves the final risk score in one step."""
    init_db(db_path)
    result = calculate_risk_score(cvss_score, epss_score, blast_radius_score)
    save_result(cve_id, asset_id, result, db_path)
    return {"cve_id": cve_id, "asset_id": asset_id, **result}


if __name__ == "__main__":
    print("Weighted Scoring Engine")
    print("=" * 40)
    cve_id = input("Enter CVE ID (e.g. CVE-2024-3400): ").strip()
    asset_id = input("Enter asset ID (e.g. payment-api-prod): ").strip()

    print("\nLooking up stored data from Task 1 and Task 2 databases...")
    cvss_score, epss_score = fetch_cvss_epss(cve_id)
    blast_radius_score = fetch_blast_radius(asset_id)

    missing = []
    if cvss_score is None:
        missing.append(f"CVSS/EPSS for {cve_id} (run Task 1's pipeline for this CVE first)")
    if blast_radius_score is None:
        missing.append(f"Blast Radius for {asset_id} (run Task 2's engine for this asset first)")

    if missing:
        print("\nCouldn't find:")
        for item in missing:
            print(f"  - {item}")
        print("\nYou can enter the missing values manually instead.")
        if cvss_score is None:
            cvss_score = float(input("Enter CVSS score (0-10): ").strip())
        if epss_score is None:
            epss_score = float(input("Enter EPSS score (0-1): ").strip())
        if blast_radius_score is None:
            blast_radius_score = float(input("Enter Blast Radius score (0-100): ").strip())

    result = score_and_save(cve_id, asset_id, cvss_score, epss_score, blast_radius_score)

    print("\nFinal Risk Score (also saved to risk_scores.db):")
    print(result)
