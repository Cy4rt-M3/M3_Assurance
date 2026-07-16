# Blast Radius Engine (Pod Quasar - Task 2)

Scores how much impact a compromised asset could have (0-100), based on
its network exposure, business criticality, and how many other systems
it's connected to. No external APIs involved - purely local calculation.

## What's in this folder

| File | Purpose |
|---|---|
| `database.py` | Defines the `blast_radius_scores` database table |
| `blast_radius_engine.py` | Scoring logic + saves results to the database + interactive input |
| `api.py` | Web API (FastAPI) exposing scoring as HTTP endpoints |
| `test_blast_radius.py` | Automated tests (no internet needed - all logic is local) |
| `requirements.txt` | Python libraries this project depends on |

## Setup (first time only)

```
python -m pip install -r requirements.txt
```

## Running interactively (asks you for asset details)

```
python blast_radius_engine.py
```

You'll be prompted for an asset ID, exposure level, criticality, and
connection count, then see the calculated score.

## Running the API

```
python -m uvicorn api:app --reload
```

Open in a browser:
```
http://127.0.0.1:8000/docs
```

- `POST /api/v1/calculate-blast-radius` — send asset details, get back the score (saved to DB)
- `GET /api/v1/blast-radius/{asset_id}` — retrieve one asset's stored score
- `GET /api/v1/blast-radius` — retrieve all stored scores, highest risk first

## Running the tests

```
python -m pytest test_blast_radius.py -v
```
Expect all tests to show `PASSED`.

## Scoring formula (assumption - confirm with your lead if a different split exists)

```
blast_radius_score = (exposure_score × 0.40) + (criticality_score × 0.35) + (connectivity_score × 0.25)
```

| Exposure level | Score |
|---|---|
| internet_facing | 100 |
| dmz | 65 |
| internal_network | 30 |
| isolated | 5 |

| Criticality | Score |
|---|---|
| critical | 100 |
| high | 75 |
| medium | 45 |
| low | 15 |

Connectivity score = `min(100, (connected_assets_count / 50) × 100)` — 50+ connections counts as maximum risk.

## Example: running it interactively

```
$ python blast_radius_engine.py
Enter asset ID (e.g. web-server-01): payment-api-prod

Network exposure level:
  1. internet_facing
  2. dmz
  3. internal_network
  4. isolated
Choose 1-4: 1

Asset criticality:
  1. critical
  2. high
  3. medium
  4. low
Choose 1-4: 1
Number of other assets it can connect to: 22

Result (also saved to blast_radius.db):
{'asset_id': 'payment-api-prod', 'exposure_level': 'internet_facing', 'criticality': 'critical',
 'connected_assets_count': 22, 'exposure_score': 100.0, 'criticality_score': 100.0,
 'connectivity_score': 44.0, 'blast_radius_score': 86.0}
```

**Reading this result:** `payment-api-prod` is internet-facing (max exposure risk),
marked as business-critical (max criticality risk), and connects to 22 other
systems (moderate connectivity risk). Combined, it scores **86 out of 100** —
high blast radius, meaning a compromise here could do serious, wide-reaching damage.

By contrast, an isolated, low-value test box with 1 connection would score
under 15 — barely any blast radius at all.

## Example: using the API

Request (`POST /api/v1/calculate-blast-radius`):
```json
{
  "asset_id": "payment-api-prod",
  "exposure_level": "internet_facing",
  "criticality": "critical",
  "connected_assets_count": 22
}
```

Response (`200 OK`):
```json
{
  "asset_id": "payment-api-prod",
  "exposure_level": "internet_facing",
  "criticality": "critical",
  "connected_assets_count": 22,
  "exposure_score": 100.0,
  "criticality_score": 100.0,
  "connectivity_score": 44.0,
  "blast_radius_score": 86.0
}
```

Then `GET /api/v1/blast-radius/payment-api-prod` returns that same stored record anytime later.

## Notes

- Re-scoring the same `asset_id` updates its existing row instead of creating a duplicate.
- Data stored in `blast_radius.db`, a SQLite file created automatically.
