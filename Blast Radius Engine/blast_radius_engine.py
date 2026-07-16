"""
Blast Radius Engine (Task 2) - core scoring logic.

Estimates the "blast radius" of an asset: if this asset gets
compromised, how much damage could spread? Combines three factors:

  - Network Exposure   (40%) - how reachable is it?
  - Asset Criticality  (35%) - how important is it to the business?
  - Blast Connectivity (25%) - how many other systems could it affect?

ASSUMPTION (flag to your team lead if they have specific weights):
these percentages mirror the Resilience Score's 40/35/25 split for
consistency - adjust freely if a different split is specified elsewhere.

No external APIs are involved - this is entirely local calculation.
"""

import logging

from database import BlastRadiusScore, get_session, init_db

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("blast_radius_engine")

EXPOSURE_SCORES = {
    "internet_facing": 100,
    "dmz": 65,
    "internal_network": 30,
    "isolated": 5,
}

CRITICALITY_SCORES = {
    "critical": 100,
    "high": 75,
    "medium": 45,
    "low": 15,
}

CONNECTIVITY_CAP = 50  # connections at/above this count score as maximum risk


def _connectivity_score(
    connected_assets_count: int, cap: int = CONNECTIVITY_CAP
) -> float:
    if connected_assets_count < 0:
        raise ValueError("connected_assets_count cannot be negative")
    return min(100.0, (connected_assets_count / cap) * 100)


def calculate_blast_radius(
    asset_id: str,
    exposure_level: str,
    criticality: str,
    connected_assets_count: int,
) -> dict:
    """
    Computes the Blast Radius score (0-100) for one asset.
    Raises ValueError if exposure_level/criticality aren't recognized,
    or if connected_assets_count is negative - callers should catch
    this and report a clear error rather than let it crash silently.
    """
    exposure_level = exposure_level.strip().lower()
    criticality = criticality.strip().lower()

    if exposure_level not in EXPOSURE_SCORES:
        raise ValueError(
            f"Unknown exposure_level '{exposure_level}'. "
            f"Expected one of: {list(EXPOSURE_SCORES.keys())}"
        )
    if criticality not in CRITICALITY_SCORES:
        raise ValueError(
            f"Unknown criticality '{criticality}'. "
            f"Expected one of: {list(CRITICALITY_SCORES.keys())}"
        )

    exposure_score = EXPOSURE_SCORES[exposure_level]
    criticality_score = CRITICALITY_SCORES[criticality]
    connectivity_score = _connectivity_score(connected_assets_count)

    blast_radius_score = (
        (exposure_score * 0.40)
        + (criticality_score * 0.35)
        + (connectivity_score * 0.25)
    )

    return {
        "asset_id": asset_id.strip(),
        "exposure_level": exposure_level,
        "criticality": criticality,
        "connected_assets_count": connected_assets_count,
        "exposure_score": float(exposure_score),
        "criticality_score": float(criticality_score),
        "connectivity_score": round(connectivity_score, 2),
        "blast_radius_score": round(blast_radius_score, 2),
    }


def save_result(result: dict, db_path: str = "blast_radius.db") -> None:
    """
    Saves one asset's Blast Radius result to the database.

    If this asset already has a stored score, that row is UPDATED in
    place (upsert) instead of creating a duplicate - so re-scoring the
    same asset always reflects the latest calculation, one row per asset.
    """
    session = get_session(db_path)
    try:
        existing = (
            session.query(BlastRadiusScore)
            .filter(BlastRadiusScore.asset_id == result["asset_id"])
            .first()
        )

        if existing:
            existing.exposure_level = result["exposure_level"]
            existing.criticality = result["criticality"]
            existing.connected_assets_count = result["connected_assets_count"]
            existing.exposure_score = result["exposure_score"]
            existing.criticality_score = result["criticality_score"]
            existing.connectivity_score = result["connectivity_score"]
            existing.blast_radius_score = result["blast_radius_score"]
        else:
            row = BlastRadiusScore(
                asset_id=result["asset_id"],
                exposure_level=result["exposure_level"],
                criticality=result["criticality"],
                connected_assets_count=result["connected_assets_count"],
                exposure_score=result["exposure_score"],
                criticality_score=result["criticality_score"],
                connectivity_score=result["connectivity_score"],
                blast_radius_score=result["blast_radius_score"],
            )
            session.add(row)

        session.commit()
    finally:
        session.close()


def score_and_save(
    asset_id: str,
    exposure_level: str,
    criticality: str,
    connected_assets_count: int,
    db_path: str = "blast_radius.db",
) -> dict:
    """Calculates and saves one asset's Blast Radius score in one step."""
    init_db(db_path)
    result = calculate_blast_radius(
        asset_id, exposure_level, criticality, connected_assets_count
    )
    save_result(result, db_path)
    return result


def _prompt_choice(label: str, options: dict) -> str:
    """Helper for the interactive CLI: shows numbered options, returns the chosen key."""
    keys = list(options.keys())
    print(f"\n{label}:")
    for i, key in enumerate(keys, start=1):
        print(f"  {i}. {key}")
    while True:
        choice = input(f"Choose 1-{len(keys)}: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            return keys[int(choice) - 1]
        print("Invalid choice, try again.")


if __name__ == "__main__":
    # Takes asset details from the person running the script.
    asset_id = input("Enter asset ID (e.g. web-server-01): ").strip()
    exposure_level = _prompt_choice("Network exposure level", EXPOSURE_SCORES)
    criticality = _prompt_choice("Asset criticality", CRITICALITY_SCORES)

    while True:
        raw_count = input("Number of other assets it can connect to: ").strip()
        if raw_count.isdigit():
            connected_assets_count = int(raw_count)
            break
        print("Please enter a whole number (0 or more).")

    result = score_and_save(
        asset_id, exposure_level, criticality, connected_assets_count
    )

    print("\nResult (also saved to blast_radius.db):")
    print(result)
