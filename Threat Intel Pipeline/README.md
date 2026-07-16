# Threat Intel Integration Pipeline (Pod Quasar - Task 1)

Fetches CVSS severity scores (from NVD) and EPSS exploit-probability
scores (from FIRST.org) for a given CVE, stores them in a database,
and exposes everything through a web API.

## What's in this folder

| File | Purpose |
|---|---|
| `database.py` | Defines the `threat_intel` database table |
| `threat_intel_pipeline.py` | Fetches CVSS/EPSS and saves results to the database |
| `api.py` | Web API (FastAPI) exposing the pipeline as HTTP endpoints |
| `test_threat_intel.py` | Automated tests (mocked, no internet required) |
| `requirements.txt` | Python libraries this project depends on |

## Setup (first time only)

1. Install Python 3.10+ from [python.org](https://python.org) if not already installed
2. Open a terminal in this folder
3. Install dependencies:
   ```
   python -m pip install -r requirements.txt
   ```

## Running the API

```
python -m uvicorn api:app --reload
```

Leave this running, then open in a browser:
```
http://127.0.0.1:8000/docs
```

This gives an interactive page to try both endpoints:
- `POST /api/v1/enrich-cves` — send `{"cve_ids": ["CVE-2024-3400"]}` to fetch + store new data
- `GET /api/v1/threat-intel/{cve_id}` — retrieve stored data for one CVE
- `GET /api/v1/threat-intel` — retrieve everything stored so far

Stop the server anytime with `Ctrl+C`.

## Example: running it interactively

```
$ python threat_intel_pipeline.py
Enter CVE ID(s) to enrich, separated by commas (e.g. CVE-2024-3400, CVE-2021-44228): CVE-2024-3400

Results (also saved to threat_intel.db):
{'cve_id': 'CVE-2024-3400', 'cvss_score': 10.0, 'severity': 'CRITICAL',
 'epss_score': 0.99999, 'epss_percentile': 1.0, 'status': 'ok', 'error': None}
```

**Reading this result:** `CVE-2024-3400` (a real, well-known critical firewall
vulnerability) comes back with the maximum possible CVSS score (**10.0**,
`CRITICAL`), and an EPSS score of **0.99999** — essentially certain to be
actively exploited in the wild. Together these tell you this is a
"drop everything and patch it" vulnerability, not just a theoretical risk.

If a CVE ID is invalid or a lookup fails, you'd instead see something like:
```
{'cve_id': 'NOT-A-REAL-CVE', 'cvss_score': None, 'severity': None,
 'epss_score': None, 'epss_percentile': None, 'status': 'error',
 'error': 'Invalid CVE ID format (expected e.g. CVE-2024-12345)'}
```
Note the batch keeps going even when one CVE fails — you get a clear
per-CVE status instead of the whole run crashing.

## Example: using the API

Request (`POST /api/v1/enrich-cves`):
```json
{
  "cve_ids": ["CVE-2024-3400"]
}
```

Response (`200 OK`):
```json
[
  {
    "cve_id": "CVE-2024-3400",
    "cvss_score": 10.0,
    "severity": "CRITICAL",
    "epss_score": 0.99999,
    "epss_percentile": 1.0,
    "status": "ok",
    "error": null
  }
]
```

Then `GET /api/v1/threat-intel/CVE-2024-3400` returns that same stored record anytime later, without hitting NVD/FIRST.org again.

## Running the tests

In a separate terminal (the API doesn't need to be running for this):
```
python -m pytest test_threat_intel.py -v
```
Expect all tests to show `PASSED`, ending in a line like `16 passed in 0.0Xs`.
These tests use mocked API responses, so they run instantly with no internet
required and can't be affected by NVD/FIRST.org being slow or rate-limited.

## Notes

- Data is stored in `threat_intel.db`, a SQLite file created automatically
  the first time the API or pipeline runs. No separate database server needed.
- No API key is required for NVD or FIRST.org at this usage volume.
- Requires an internet connection only when actually calling `/enrich-cves`
  (fetching new data) — not for running tests or starting the server.
