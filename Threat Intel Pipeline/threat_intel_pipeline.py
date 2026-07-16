"""
Threat Intel Integration Pipeline - core enrichment logic.

Given a CVE ID, fetches CVSS (from NVD) and EPSS (from FIRST.org),
combines them, and saves the result to the database via database.py.

Reliability:
  - Invalid CVE IDs are rejected before any network call.
  - Transient network failures (timeouts, 429, 5xx) are retried with backoff.
  - One CVE's failure never crashes the rest of a batch.
"""

import re
import time
import logging
from datetime import datetime

import requests

from database import ThreatIntel, get_session, init_db

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("threat_intel_pipeline")

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
FIRST_EPSS_URL = "https://api.first.org/data/v1/epss"

CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)

MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 15
DELAY_BETWEEN_CALLS_SECONDS = 0.6


def is_valid_cve_id(cve_id: str) -> bool:
    return bool(CVE_PATTERN.match(cve_id.strip()))


def _get_with_retry(url: str, params: dict) -> requests.Response:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)

            if response.status_code == 429 or response.status_code >= 500:
                wait = BACKOFF_BASE_SECONDS**attempt
                logger.warning(
                    "Retrying %s after status %s (wait %ss)",
                    url,
                    response.status_code,
                    wait,
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            last_error = exc
            wait = BACKOFF_BASE_SECONDS**attempt
            logger.warning(
                "Network error on %s (attempt %s/%s): %s. Retrying in %ss",
                url,
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts"
    ) from last_error


def get_cvss_score(cve_id: str) -> dict:
    try:
        response = _get_with_retry(NVD_API_URL, {"cveId": cve_id})
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("CVSS lookup failed for %s: %s", cve_id, exc)
        return {"cvss_score": None, "severity": None, "error": str(exc)}

    vulnerabilities = data.get("vulnerabilities", [])
    if not vulnerabilities:
        return {"cvss_score": None, "severity": None, "error": None}

    metrics = vulnerabilities[0].get("cve", {}).get("metrics", {})
    for version_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if version_key in metrics and metrics[version_key]:
            cvss_data = metrics[version_key][0].get("cvssData", {})
            return {
                "cvss_score": cvss_data.get("baseScore"),
                "severity": cvss_data.get("baseSeverity"),
                "error": None,
            }

    return {"cvss_score": None, "severity": None, "error": None}


def get_epss_score(cve_id: str) -> dict:
    try:
        response = _get_with_retry(FIRST_EPSS_URL, {"cve": cve_id})
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("EPSS lookup failed for %s: %s", cve_id, exc)
        return {"epss_score": None, "percentile": None, "error": str(exc)}

    results = data.get("data", [])
    if not results:
        return {"epss_score": None, "percentile": None, "error": None}

    result = results[0]
    try:
        return {
            "epss_score": float(result["epss"]),
            "percentile": float(result["percentile"]),
            "error": None,
        }
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Unexpected EPSS response shape for %s: %s", cve_id, exc)
        return {"epss_score": None, "percentile": None, "error": str(exc)}


def enrich_cve(cve_id: str) -> dict:
    """Fetches CVSS + EPSS for one CVE. Never raises - failures go in 'error'."""
    cve_id = cve_id.strip().upper()

    if not is_valid_cve_id(cve_id):
        return {
            "cve_id": cve_id,
            "cvss_score": None,
            "severity": None,
            "epss_score": None,
            "epss_percentile": None,
            "status": "error",
            "error": "Invalid CVE ID format (expected e.g. CVE-2024-12345)",
        }

    cvss = get_cvss_score(cve_id)
    time.sleep(DELAY_BETWEEN_CALLS_SECONDS)
    epss = get_epss_score(cve_id)

    errors = [e for e in (cvss.get("error"), epss.get("error")) if e]

    return {
        "cve_id": cve_id,
        "cvss_score": cvss["cvss_score"],
        "severity": cvss["severity"],
        "epss_score": epss["epss_score"],
        "epss_percentile": epss.get("percentile"),
        "status": "error" if errors else "ok",
        "error": "; ".join(errors) if errors else None,
    }


def dedupe_cve_ids(cve_ids: list) -> list:
    """
    Removes duplicate CVE IDs from a list (case-insensitive, ignores
    surrounding whitespace), keeping the first occurrence's original order.

    e.g. ["CVE-2024-3400", "cve-2024-3400", "CVE-2021-44228"]
      -> ["CVE-2024-3400", "CVE-2021-44228"]
    """
    seen = set()
    deduped = []
    for cve_id in cve_ids:
        normalized = cve_id.strip().upper()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(cve_id.strip())
    return deduped


def save_result(result: dict, db_path: str = "threat_intel.db") -> None:
    """
    Saves one enrichment result to the database.

    If this CVE already has a stored record, that record is UPDATED
    in place (upsert) instead of creating a duplicate row - so
    re-enriching the same CVE keeps the database at one row per CVE,
    always reflecting the latest lookup.
    """
    session = get_session(db_path)
    try:
        existing = (
            session.query(ThreatIntel)
            .filter(ThreatIntel.cve_id == result["cve_id"])
            .first()
        )

        if existing:
            existing.cvss_score = result["cvss_score"]
            existing.severity = result["severity"]
            existing.epss_score = result["epss_score"]
            existing.epss_percentile = result["epss_percentile"]
            existing.status = result["status"]
            existing.error = result["error"]
            existing.fetched_at = datetime.utcnow()
        else:
            row = ThreatIntel(
                cve_id=result["cve_id"],
                cvss_score=result["cvss_score"],
                severity=result["severity"],
                epss_score=result["epss_score"],
                epss_percentile=result["epss_percentile"],
                status=result["status"],
                error=result["error"],
            )
            session.add(row)

        session.commit()
    finally:
        session.close()


def enrich_and_save(cve_ids: list, db_path: str = "threat_intel.db") -> list:
    """
    Enriches each CVE and saves the result to the database.
    Duplicate CVE IDs in the input are removed first (see dedupe_cve_ids),
    so the same CVE is never fetched or stored twice in one batch.
    One CVE's failure (network or otherwise) does not stop the rest.
    """
    init_db(db_path)  # make sure the table exists

    unique_cve_ids = dedupe_cve_ids(cve_ids)
    skipped = len(cve_ids) - len(unique_cve_ids)
    if skipped:
        logger.info("Skipped %s duplicate CVE ID(s) in this batch", skipped)

    results = []
    for cve_id in unique_cve_ids:
        logger.info("Processing %s...", cve_id)
        try:
            result = enrich_cve(cve_id)
        except Exception as exc:  # noqa: BLE001 - batch-level safety net
            logger.error("Unexpected failure enriching %s: %s", cve_id, exc)
            result = {
                "cve_id": cve_id,
                "cvss_score": None,
                "severity": None,
                "epss_score": None,
                "epss_percentile": None,
                "status": "error",
                "error": str(exc),
            }
        save_result(result, db_path)
        results.append(result)
        time.sleep(DELAY_BETWEEN_CALLS_SECONDS)
    return results


if __name__ == "__main__":
    # Takes CVE IDs from the person running the script, instead of a
    # hardcoded list. Enter one or more CVE IDs separated by commas.
    user_input = input(
        "Enter CVE ID(s) to enrich, separated by commas "
        "(e.g. CVE-2024-3400, CVE-2021-44228): "
    )
    requested_cves = [cve.strip() for cve in user_input.split(",") if cve.strip()]

    if not requested_cves:
        print("No CVE IDs entered. Exiting.")
    else:
        enriched = enrich_and_save(requested_cves)

        print("\nResults (also saved to threat_intel.db):")
        for record in enriched:
            print(record)
