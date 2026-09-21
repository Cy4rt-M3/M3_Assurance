# Project Completion — Step Log

Goal: Complete the CyBreach Assurance module end-to-end (backend first),
using branch assets where they already exist, driven by the OCSF input
`~/Downloads/sample_ocsf_logs.json`.

Reference docs:
- Technical Doc v2.0 (extracted from PDF → `/tmp/opencode/pdf_extract.md`)
- `Assurance_Project_Execution_Plan.md` (`~/Downloads/`)
- Branch diff map → `BRANCH_DIFFS.md`

Status markers: `[done]` `[in-progress]` `[blocked]` `[pending]`

---

## Step 1 — Validate input & baseline state

**Input file:** `/home/d33/Downloads/sample_ocsf_logs.json`

Contents (1 event):
```json
{ "class_uid": 4001, "category_uid": 4, "activity_id": 1, "severity_id": 1,
  "type_uid": 400101, "metadata": {"version": "1.1.0", "product":
  {"name": "PodGamma", "vendor_name": "Cybreach"}},
  "disposition": "Allowed", "action": "Allowed" }
```

Observations:
- OCSF `category_uid=4` → **Findings**; `class_uid=4001` → **Security Finding**;
  `type_uid=400101` → Security Finding : **Create**.
- Very sparse: no `type_name`, `technique`, `attack/` mapping, no evidence
  hash, no `engagement_id`. The real Module-2 verdict would carry
  `outcome` (Detected/Missed/Partial/No Data), `technique_id` (ATT&CK),
  `evidence_hash`, `engagement_id`.
- Implication: ingestion must tolerate missing fields and derive defaults from
  OCSF IDs (map `4001` → a default "scanning" technique, `disposition` →
  outcome translation).

**Baseline git state (before any change):**
- Branch: `main` @ `da59f15`.
- `apps/` (8 packages): control_mapping, evidence_aggregator, framework_registry,
  gap_analyzer, report_generator, report_publisher, resilience_scorer, shared.
- `contracts/`: 6 frozen v1.0 JSON schemas (control_mapping, evidence_link,
  gap_analysis, report_delivery, resilience_score, compliance_report).
- `tests/`: one test module per service + shared + conftest.
- `alembic/versions/0001_initial_schema.py`: single initial migration.
- Services on main expose **only `/health`** — business logic lives in branches.

---

## Step 2 — Audit reusable branch assets

Completed. Key facts recorded in `BRANCH_DIFFS.md` + audit notes:

- **Registry (Selva_G2005 / Pod4):** `loader.py` (in-memory JSON, lru_cache) +
  `definitions/*.json` — **8 frameworks, 491 controls, 585 crosswalks** (all
  `equivalence_level: "Unknown"`). Real endpoints: `GET /frameworks`,
  `GET /frameworks/{id}/controls`, `GET /controls/{id}/crosswalks`.
- **Evidence (Pod2):** `repository.py` (SQL: create/get evidence links,
  summary via `EXISTS`), endpoints `POST/GET /evidence-links`,
  `GET /evidence-summary/{engagement_id}`.
- **Scoring (feat/quasar):** `blast_radius.py` (pure), `weighted_risk_score`
  (50/30/20) in `calculator.py`. NVD/EPSS fetchers are live-HTTP dependent →
  decided NOT to port into core pipeline (tests must stay deterministic,
  project forbids mocks); keep as documented future work. Risk scored locally
  from OCSF severity instead.
- **Nebula:** full reportlab renderer but separate orphan codebase, deps
  incomplete (playwright missing) → not reused; we build a self-contained
  HTML report generator that matches the `compliance_report.v1.json` contract.

**Assets already checked out into `main` working tree:**
`apps/framework_registry/loader.py`, `apps/framework_registry/definitions/*.json`,
`apps/evidence_aggregator/repository.py`, `apps/resilience_scorer/blast_radius.py`.

---

## Step 3 — Design (end-to-end backend pipeline)

Target flow (matches Tech Doc §4 core workflow):
```
OCSF event(s)                                   [input: Downloads/sample_ocsf_logs.json]
  → 1. Ingestion   → verdict (outcome, technique, severity, evidence_hash) + evidence link  [evidence_aggregator + shared/ocsf]
  → 2. Control map → control statuses (Met/Not Met/Partial) + coverage_pct                  [control_mapping]
  → 3. Evidence    → summary (total/unique/completeness_pct)                                 [evidence_aggregator]
  → 4. Score       → composite(40/35/25) + band, persisted history                           [resilience_scorer]
  → 5. Gaps        → uncovered_control / missed_detection / evidence_gap + remediation       [gap_analyzer]
  → 6. Report      → HTML compliance report + sha256 content_hash                            [report_generator]
  → 7. Delivery    → download delivery record (delivered)                                    [report_publisher]
```
Orchestrated by `apps/pipeline/engine.run_pipeline()` + CLI `python -m apps.pipeline.run`.

**Design decisions**
1. **OCSF→verdict translation** (`apps/shared/ocsf.py`, new): `class_uid=4001`
   → Security Finding; default ATT&CK technique `T1078`; disposition map:
   `Blocked|Detected→Detected`, `Allowed→Detected`, `Missed→Missed`,
   `No Data|None→No Data`, else `Partial`; severity_id 1→Informational...
   5→Critical; evidence_hash = sha256(canonical JSON of the event).
2. **DB persistence** via raw SQL `text()` (matches Pod2 style) on the existing
   tables + new migration `0002` adding `engagements`, `verdicts`, `deliveries`.
3. **Technique→control resolution** reads the DB `controls.attack_mapping`
   (array contains technique), filtered by `framework_ids`; control statuses must
   satisfy FK → in tests the 10 fixture controls are seeded by `conftest`.
4. **Hard rule** honored: control Met only when every mapped technique has a
   Detected verdict with linked evidence; Missed/No Data → Not Met; Partial → Partial.
5. **Score** reuses existing `calculator.py` (40/35/25 + bands) — weights already match.
6. **Report** string-rendered HTML (no Jinja dep added); contains exec summary,
   composite/component scores + band, per-framework control table, evidence refs,
   gap/remediation list; `content_hash = sha256(content)`.
7. **No new runtime deps** (openpyxl/pymongo images stay on Pod1 branch only;
   MongoDB not required for this pipeline).

---

## Step 4 — Audit side-effects (things that must not break)

- `guard-my-code.py` + CI enforce: 100% coverage (`apps`), ruff (McCabe ≤4),
  pyright strict, vulture 100-confidence, bandit, detect-secrets, pip-audit.
  All new code must satisfy these.
- Tests hit real Postgres+Redis (conftest seeds `frameworks`+`controls` only).
- `test_control_mapping.py` asserts `/health` db AND redis are True.

---

## Step 5 — Implementation (completed)

All services implemented against the Step-3 design; every change live on
`main` (uncommitted, staged in working tree on top of `da59f15`).

**New / extended service code**
- `apps/shared/ocsf.py` — OCSF → verdict translation (`verdict_data`,
  `technique_id_from_event`, `outcome_from_disposition`, `severity_id_from_event`,
  `evidence_hash` sha256).
- `apps/evidence_aggregator/` — `ensure_engagement`, `create_verdict`,
  `list_verdicts`, `get_verdict`, `create_evidence_link`, `get_evidence_link`,
  `get_evidence_links`, `get_evidence_summary` (correctly scoped per
  engagement via `JOIN verdicts`), `count_verdicts`; handlers
  `ingest_ocsf` (idempotent skip of existing verdicts), `evidence_summary`,
  `verdict_detail`, `create_link` with explicit 409 pre-check; migration
  `0002` (engagements/verdicts) and later `0003`/`0004`.
- `apps/control_mapping/` — `mapper.py` (`build_mapping`, `mapped_control_status`
  worst-case, `effective_mapping` crosswalk aware), `repository.py`
  (`list_controls_for_techniques`, `get_control_statuses`, `upsert_control_statuses`
  with evidence hashes), handlers `map_controls`, `control_statuses` handling
  missing-engagement default.
- `apps/framework_registry/` — real `seed()` + `build_session_factory_from_settings()`;
  definitions JSON ported (8 frameworks, 491 controls, 585 crosswalks).
- `apps/resilience_scorer/` — `calculate_score` (40/35/25, bands) persisting
  history; `weighted_risk_score` local-only (no live NVD/EPSS by design).
- `apps/gap_analyzer/` — `analyze` (uncovered_control / missed_detection /
  evidence_gap with dedup + remediation), `save_gaps`/`list_gaps`; summary handler.
- `apps/report_generator/` — self-contained HTML renderer (`_render_score`,
  `_render_controls`, `_render_gaps`, `_render_verdicts`), `generate_report`
  with `content_hash = sha256(content)`, `report_detail`.
- `apps/report_publisher/` — channels `download`/`email`/`webhook`, `publish`
  (404 for unknown report, 422 for unsupported channel), sequence-based
  `delivery_id` (multiple deliveries per report), `list_deliveries`.
- `apps/pipeline/` — `engine.run_pipeline` (ingest → map → evidence → score →
  gaps → report), idempotent link/verdict skips via existence pre-checks;
  CLI `python -m apps.pipeline`.

**Bug fixes during test hardening**
- `get_evidence_summary` scoping (evidence leaked across engagements).
- `report_publisher` `delivery_id` was fixed per report (second publish crashed).
- `ingest_ocsf` skipped existing rows for true idempotency.
- Duplicate-link 409 restructured to a pre-check (avoids a coverage tracer
  limitation where a `raise` following an `await` in an `except` was never
  attributed to a source line).

**Test suite (`tests/`)**
- Added direct async-handler tests (`test_handlers_direct.py`) because the
  coverage tracer (ctracer) does not attribute post-`await` lines when handlers
  run through the ASGI HTTP transport; direct coroutine calls do.
- Added unit tests for uncovered branches: `_verdict_outcome` default,
  `mapped_control_status` worst-first weight order, `evidence_hash_map` skip
  semantics, `_first_candidate_control` none-found, `severity_id` parsing,
  `build_session_factory_from_settings`, report render helpers, publish
  delivered/failed/404/422, summary default/explicit completeness.
- conftest: session autouse `seed_db` truncates the 11 tables and reloads the
  fixture registry; `service_apps_on_test_db` repoints every service `_engine`
  / `_session_factory` at the test DB.

---

## Step 6 — Quality gates (all passing)     [done]

| Gate | Result |
|---|---|
| `pytest --cov=apps --cov-fail-under=100` | **171 passed, 100.00 % coverage (0 missed stmts, 0 partial branches)** |
| `ruff check .` (E/F/I/B/UP/C90, McCabe ≤4) | clean — 4 complex functions refactored below threshold |
| `ruff format` | applied (39 files reformatted) |
| `pyright` strict (apps + tests) | 0 errors — fixture params annotated, `+asyncpg` typing fixed |
| `vulture --min-confidence 100` | clean |
| `bandit -r apps` | 0 Medium, 0 High |
| `detect-secrets scan --baseline` | passed (baseline updated) |
| `pip-audit .` | no known vulnerabilities |
| `alembic upgrade head` on test DB | 0004 (head), clean |

Coverage at 100% relies on 3 intentional choices:
1. Direct async-handler calls (above) — ASGI transport loses post-`await` lines.
2. `__main__` interpreter-entry guards excluded in `pyproject.toml`
   `[tool.coverage.report].exclude_lines`.
3. Dedicated unit tests for each remaining branch (no uncovered code paths).

---

## Step 7 — End-to-end verification (main DB)    [done]

```bash
python -m apps.pipeline ~/Downloads/sample_ocsf_logs.json --engagement-id ENG-2026-003 \
    --framework nist_csf_2_0_2 iso_27001_2022 pci_dss_v4_0_1
```
- Registry seeded (8 frameworks, 491 controls) → 1 verdict ingested
  (evidenced) → control statuses mapped → composite score **100.0 → “Resilient”**
  → zero gaps → HTML report persisted with sha256 `content_hash`
  (`ENG-2026-003-rpt-0002` on re-run proves idempotency).
- Re-runs converge (existing verdicts/links skipped) — verified twice.

**Run order to reproduce the full gate** (uv not installed here → use `.venv`):
1. `pytest tests --cov=apps --cov-report=term-missing --cov-fail-under=100 -x`
2. `ruff check .` / `ruff format --check .`
3. `pyright`
4. `vulture --exclude .venv . --min-confidence 100`
5. `bandit -r apps`
6. `detect-secrets scan --baseline .secrets.baseline`
7. `DATABASE_URL=postgresql+asyncpg://assurance:assurance@127.0.0.1:5432/assurance_test alembic upgrade head`

All steps green. Backend M3 assurance module is complete.