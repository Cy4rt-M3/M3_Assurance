# Branch Differences vs `main`

Generated: 2026-09-19 · Base: `origin/main` (`da59f15`)

Legend: `+` added · `~` modified · `-` deleted

---

## Relationship overview

| Branch | Commits ahead | Commits behind | Status vs main |
|---|---|---|---|
| origin/Bhuvana-CLI | 0 | 0 | **Identical to main** |
| origin/selva | 0 | 0 | **Identical to main** |
| origin/Docker_Integrated_Pod1 | 4 | 0 | Ahead (clean) |
| origin/Docker_Integrated_Pod2 | 1 | 0 | Ahead (clean) |
| origin/Docker_Integrated_Pod4 | 3 | 0 | Ahead (clean) |
| origin/Selva_G2005 | 1 | 0 | Ahead (clean) |
| origin/feat/nova/framework-registry-workbook | 2 | 0 | Ahead (clean) |
| origin/feat/quasar/calculator-cli | 8 | 0 | Ahead (clean) |
| origin/pod-quasar-task1-2-3 | 3 | 0 | Ahead (clean) |
| origin/nebula | 2 | 14 | **Disjoint/orphan history** |

---

## Identical to main

### `Bhuvana-CLI` and `selva`
- `git rev-list` ahead=0, behind=0 — no commits, no file changes.
- Likely stale/merged branches; safe to delete.

---

## Pod Dockerization

### `Docker_Integrated_Pod1` — Controls Importer (MongoDB)
Commits: `8cb81af` → `a2be235` → `39978de` → `5047cf1`
- `+` `Dockerfile` (8 lines) — uvicorn image for control_mapping.
- `+` `apps/controls_importer/` — new service: `main.py` (FastAPI entry) + `importer.py` (reads Excel via openpyxl, upserts into MongoDB with `pymongo` `UpdateOne`).
- `~` `.env.example` (+7), `docker-compose.yml` — added MongoDB (port 27017), postgres 5433, redis 6380.
- `~` `apps/shared/settings.py` — DB ports → 5433, redis → 6380, **new MongoDB + controls source settings** (`mongodb_url`, `controls_file`, `controls_sheet`).
- `~` `alembic.ini` / `alembic/env.py` — port 5433, removed hard-coded feature flags.
- `+` `data/controls/Pod_Nova_Framework_Registry_updated.xlsx` + `Pod_Nova_Framework_Registry_updated.xlsx` — workbook seed data.
- `~` `pyproject.toml` / `uv.lock` — added `openpyxl`, `pymongo`.

### `Docker_Integrated_Pod2` — Evidence Aggregator
Commits: `9cbe536`
- `+` `Dockerfile` (23 lines).
- `+` `apps/evidence_aggregator/repository.py` — SQLAlchemy async repo: `create_evidence_link`, `get_evidence_links`, `get_evidence_summary`.
- `~` `apps/evidence_aggregator/main.py` — real endpoints replacing placeholder: `POST /evidence-links`, `GET /evidence-links`, `GET /evidence-summary`, proper DB sessions (returns 409/404/422).
- `+` `docker/seed/seed.py` — seeds evidence_links sample rows.
- `~` `docker-compose.yml` (+126) — evidence-aggregator container; `README.md` (+92) — Pod 2 Docker guide.

### `Docker_Integrated_Pod4` — Framework Registry + Frontend Dashboard
Commits: `c8200f6` → `9df8012` → `6b08074`
- `+` `Dockerfile.framework_registry` — uv-based slim image, serves port 10006.
- `+` `apps/framework_registry/definitions/{frameworks,controls,crosswalks}.json` and `apps/framework_registry/loader.py` — real registry data + loader.
- `~` `apps/framework_registry/main.py` — **real data endpoints**: `GET /frameworks`, `GET /frameworks/{id}/controls`, `GET /controls/{id}/crosswalks` (replacing mock stubs).
- `~` `docker-compose.yml`, `README.md`.
- `+` **full React/Next.js frontend** (`frontend/`, ~120 files, ~30k LOC): Next 14 + Tailwind + shadcn/ui components, assurance dashboard (frameworks, evidence, risk, reports, tasks), real-framework data hooks, API routes (`/api/frameworks`, `/api/frameworks/[id]/controls`), Caddyfile + Dockerfile, prisma schema.
- `+` `tests/test_framework_registry.py` (101 lines).
- **Note:** this branch includes the same framework-registry data + loader + tests as `Selva_G2005`.

---

## Framework Registry

### `Selva_G2005`
Commits: `c8200f6`
- `+` `apps/framework_registry/definitions/*.json` — registry data: `frameworks.json` (74 lines), `controls.json` (~5,182 lines), `crosswalks.json` (~2,927 lines).
- `+` `apps/framework_registry/loader.py` (57 lines) — loads the JSON on startup for the new endpoints.
- `~` `apps/framework_registry/main.py` — adds the 3 real data endpoints (same content as Pod4 above).
- `~` `tests/test_framework_registry.py` (+101) — tests loader + endpoints.
- **Subset of** `Docker_Integrated_Pod4` (registry code only, no Docker/frontend).

### `feat/nova/framework-registry-workbook`
Commits: `8cb81af` → `a2be235`
- `+` `Pod_Nova_Framework_Registry_updated.xlsx` — framework/control workbook (input seed).
- `~` `alembic.ini` (5433→5432), `apps/shared/settings.py` (±6) — port alignment only.
- Subset already contained in `Docker_Integrated_Pod1`/`Pod4`.

---

## Quasar — Resilience Scorer / Calculator

### `feat/quasar/calculator-cli`
Commits: `856e40d` → `fb5b5ce` → `6d7b484` → `1f98b63` → `a75d873` → `d4e6ad6` → `69bbca2` → `84c2d0e`
- `+` `app/Calculator.py` — Python CLI calculator for resilience scoring.
- `+` `apps/resilience_scorer/threat_intel.py` — async fetchers: NVD CVSS score, FIRST.org EPSS probability (httpx, 10s timeout).
- `+` `apps/resilience_scorer/blast_radius.py` — blast-radius scoring (exposure + criticality + internet-facing, 0–100 cap).
- `~` `apps/resilience_scorer/calculator.py` — weighted risk scoring integrated with threat intel.
- `~` `apps/resilience_scorer/main.py` (+83) — new endpoints wiring threat-intel/blast-radius/weighted scores.
- `~` `apps/resilience_scorer/models.py` (+41) — request/response models (CVE, EPSS, blast radius, weighted risk).
- Rigorous quality pass: Ruff formatting, Pyright type hints, complexity reduction.

### `pod-quasar-task1-2-3`
Commits: `7964be1` → `3534e3c` → `b84ad82`
- `+` Standalone engines under top-level dirs (sunburst from the CLI attempt):
  - `Threat Intel Pipeline/` — async pipeline + FastAPI `api.py`, SQLite `database.py`, 276-line `threat_intel_pipeline.py`, tests (237 lines).
  - `Blast Radius Engine/` — 189-line engine + `api.py`, SQLite DB, tests (114 lines).
  - `Weighted Scoring Engine/` — 244-line engine + `api.py`, tests (163 lines).
- `+` `apps/Calculator.py` (18 lines) — CLI entry.
- **Note:** these are standalone folders (with committed SQLite `.db` + `.pyc`-style artifacts) vs the `feat/quasar/calculator-cli` approach of integrating into `apps/resilience_scorer/`.

---

## Disjoint history

### `nebula`
Commits: `9511aa6` (first commit) → `12bf149` (pin pydantic, jinja2, reportlab)
- **Freestanding, unrelated codebase** — no merge base with `main`.
- A complete Report Engineering microservice under `app/`:
  - `report_service/` — builders (cover, dashboard, executive summary, appendix), audience filter + profiles (board/ciso/customer/executive/technical), collectors (asset, compliance, evidence, finding, metadata), normalizers, recommendation + risk + statistics engines.
  - `renderer/` + `pdf/` + `templates/` (HTML templates) — HTML/PDF rendering via Jinja2/WeasyPrint-style flow, `reportlab` used.
  - `storage/` (local / S3 / MinIO), `workers/` (Celery), `services/` (chart, pdf, report, storage).
  - `docs/`, `scripts/`, sample reports.
- **Anti-patterns:** commits `.env`, `__pycache__/*.pyc`, `.db` and generated PDF artifacts; `README.md` and `app/main.py` are empty files; pinning via `requirments.txt` (sic) not `pyproject.toml`.

---

## What is NOT in main (aggregate)

1. MongoDB-based controls importer + Excel workbook data (Pod1).
2. Real evidence-link persistence + seed data (Pod2).
3. Full framework registry JSON data + loader + 3 real endpoints (Pod4 / Selva_G2005).
4. Complete Next.js/React assurance dashboard frontend (Pod4).
5. Threat-intel / blast-radius / weighted-risk scoring for resilience_scorer (Quasar branches) — both as integrated modules and standalone engines.
6. A standalone report-generation (PDF) service (`nebula`) — entirely different from main's `apps/report_generator/` and would need rebasing onto `apps/` structure to merge.