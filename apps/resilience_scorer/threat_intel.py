"""Threat Intelligence helper functions."""

from typing import Any

import httpx

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_API = "https://api.first.org/data/v1/epss"


def _extract_cvss(metrics: dict[str, Any]) -> float:
    if "cvssMetricV31" in metrics:
        return float(metrics["cvssMetricV31"][0]["cvssData"]["baseScore"])

    if "cvssMetricV30" in metrics:
        return float(metrics["cvssMetricV30"][0]["cvssData"]["baseScore"])

    return 0.0


async def fetch_cvss(cve_id: str) -> float:
    """Fetch CVSS score."""

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            NVD_API,
            params={"cveId": cve_id},
        )

    if response.status_code != 200:
        return 0.0

    data: dict[str, Any] = response.json()
    vulnerabilities = data.get("vulnerabilities", [])

    if not vulnerabilities:
        return 0.0

    metrics = vulnerabilities[0]["cve"]["metrics"]

    return _extract_cvss(metrics)


async def fetch_epss(cve_id: str) -> float:
    """Fetch EPSS probability score."""

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            EPSS_API,
            params={"cve": cve_id},
        )

    if response.status_code != 200:
        return 0.0

    data: dict[str, Any] = response.json()
    records = data.get("data", [])

    if not records:
        return 0.0

    return float(records[0]["epss"])
