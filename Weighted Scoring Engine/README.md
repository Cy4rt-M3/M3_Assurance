# Weighted Scoring Engine (Pod Quasar - Task 3)

Combines the outputs of Task 1 (CVSS + EPSS) and Task 2 (Blast Radius)
into one final 0-100 risk score for a specific vulnerability affecting
a specific asset.

## What's in this folder

| File | Purpose |
|---|---|
| `database.py` | Defines the `risk_scores` database table |
| `weighted_scoring_engine.py` | Scoring logic + lookup from Task 1/2 databases + interactive input |
| `api.py` | Web API (FastAPI) exposing scoring as HTTP endpoints |
| `test_weighted_scoring.py` | Automated tests (no internet needed - all logic is local) |
| `requirements.txt` | Python libraries this project depends on |

## Setup (first time only)

```
python -m pip install -r requirements.txt
```

## The formula

```
composite_score = (CVSS × 10 × 0.40) + (EPSS × 100 × 0.35) + (Blast Radius × 0.25)
```

CVSS (0-10) and EPSS (0-1) are scaled up to 0-100 first so all three
inputs are on the same scale before weighting.

**Assumption** (task description didn't specify exact weights or bands -
confirm with your team lead): weights follow the same 40/35/25 pattern
used elsewhere in the project. Risk bands:

| Score range | Band |
|---|---|
| 85-100 | Critical |
| 65-84.9 | High |
| 40-64.9 | Medium |
| 0-39.9 | Low |

## Example: running it interactively

This mode automatically looks up CVSS/EPSS and Blast Radius from Task 1's
and Task 2's databases, if you've already scored that CVE and asset there.

```
$ python weighted_scoring_engine.py
Weighted Scoring Engine
========================================
Enter CVE ID (e.g. CVE-2024-3400): CVE-2024-3400
Enter asset ID (e.g. payment-api-prod): payment-api-prod

Looking up stored data from Task 1 and Task 2 databases...

Final Risk Score (also saved to risk_scores.db):
{'cve_id': 'CVE-2024-3400', 'asset_id': 'payment-api-prod', 'cvss_score': 10.0,
 'epss_score': 0.99999, 'blast_radius_score': 86.0, 'cvss_normalized': 100.0,
 'epss_normalized': 100.0, 'composite_score': 96.5, 'risk_band': 'Critical'}
```

**Reading this result:** this combines the real CVSS/EPSS data from Task 1
(`CVE-2024-3400` is a critical, actively-exploited firewall bug) with the
Blast Radius example from Task 2 (`payment-api-prod`, internet-facing and
critical). The combination scores **96.5/100 — Critical** risk: a severe,
actively-exploited vulnerability on a high-value, exposed asset is about
as urgent as it gets.

**If the lookup can't find data** for that CVE or asset (i.e. you haven't
run Task 1/Task 2 for them yet), it tells you what's missing and lets you
type the numbers in directly instead:
```
Couldn't find:
  - CVSS/EPSS for CVE-2024-3400 (run Task 1's pipeline for this CVE first)

You can enter the missing values manually instead.
Enter CVSS score (0-10): 10
Enter EPSS score (0-1): 0.99999
```

## Example: using the API

**Option A - automatic lookup** (`POST /api/v1/calculate-risk-score/lookup`):
```json
{
  "cve_id": "CVE-2024-3400",
  "asset_id": "payment-api-prod"
}
```

**Option B - direct values** (`POST /api/v1/calculate-risk-score`), if you
already have the three numbers and don't need Task 1/2's databases involved:
```json
{
  "cve_id": "CVE-2024-3400",
  "asset_id": "payment-api-prod",
  "cvss_score": 10.0,
  "epss_score": 0.99999,
  "blast_radius_score": 86.0
}
```

Both return the same shape (`200 OK`):
```json
{
  "cve_id": "CVE-2024-3400",
  "asset_id": "payment-api-prod",
  "cvss_score": 10.0,
  "epss_score": 0.99999,
  "blast_radius_score": 86.0,
  "cvss_normalized": 100.0,
  "epss_normalized": 100.0,
  "composite_score": 96.5,
  "risk_band": "Critical"
}
```

Then `GET /api/v1/risk-score/CVE-2024-3400/payment-api-prod` returns that
same stored record anytime later. `GET /api/v1/risk-scores` lists every
CVE/asset combination scored so far, worst risk first.

## Running the API

```
python -m uvicorn api:app --reload
```
Open: `http://127.0.0.1:8000/docs`

## Running the tests

```
python -m pytest test_weighted_scoring.py -v
```
Expect all tests to show `PASSED`, ending in a line like `15 passed in 0.0Xs`.

## Notes

- **Folder layout matters for automatic lookup**: this engine expects
  Task 1's folder (`threat_intel.db`) and Task 2's folder (`blast_radius.db`)
  to sit alongside this one, e.g.:
  ```
  ProjectRoot/
    task1_threat_intel/threat_intel.db
    task2_blast_radius/blast_radius.db
    task3_weighted_scoring/   <- this folder
  ```
  If your folders are named differently, either rename them to match, or
  just use the direct-input mode (manual entry / Option B above) instead.
- Re-scoring the same CVE + asset pair updates its existing row instead
  of creating a duplicate. The same CVE against a *different* asset is
  tracked as a separate row, since risk depends on both.
- No internet connection needed for this task - all calculation is local.
