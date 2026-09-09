
# M3 Assurance

CyArt Tech LLP — Compliance, Evidence & Resilience Scoring Engine.

---

## Requirements

| Tool | Version | Install |
|---|---|---|
| **Docker Desktop** | Latest | [Windows / Mac](https://www.docker.com/products/docker-desktop/) · [Linux](https://docs.docker.com/engine/install/) |
| **Python** | 3.12+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Git** | Any | [git-scm.com](https://git-scm.com/downloads) |

> `uv` (Python package manager) is installed automatically by the setup script if missing.

---

## Setup

Clone the repo, then run the setup script for your OS. It will:
- Install `uv` if missing
- Start Postgres + Redis via Docker
- Install all Python dependencies (`uv sync`)
- Run database migrations on both main and test databases
- Create your `.env` from `.env.example`

**Linux / macOS**
```bash
git clone https://github.com/Cy4rt-M3/M3_Assurance.git
cd M3_Assurance
chmod +x master_setup.sh
./master_setup.sh
```

**Windows (PowerShell or CMD)**
```powershell
git clone https://github.com/Cy4rt-M3/M3_Assurance.git
cd M3_Assurance
python master_setup.py
# or double-click master_setup.bat
```

---

## Running Tests

Tests hit **real Postgres + Redis** — no mocks. Run setup first.

**Linux / macOS**
```bash
./guard-my-code.sh      # full quality gate
pytest                  # tests only
```

**Windows**
```powershell
python guard-my-code.py    # full quality gate
# or: .\guard-my-code.bat
uv run pytest              # tests only
```

The quality gate runs in this order:
1. `uv sync` — sync deps
2. `uv lock --check` — lockfile up to date
3. `ruff format` — auto-format
4. `ruff check` — lint + McCabe complexity ≤4
5. `jscpd` — duplicate detection (needs Node.js)
6. `pyright` — strict type checking
7. `vulture` — dead code
8. `bandit` — security patterns
9. `detect-secrets` — no secrets in code
10. `pip-audit` — CVE scan
11. `pytest --cov-fail-under=100` — 100% coverage required

---

## Starting a Service

```bash
# All platforms
uv run uvicorn apps.control_mapping.main:app --port 10001 --reload
```

## Port Map

| Service | Port |
|---|---|
| control_mapping | 10001 |
| evidence_aggregator | 10002 |
| gap_analyzer | 10003 |
| resilience_scorer | 10004 |
| report_generator | 10005 |
| framework_registry | 10006 |
| report_publisher | 10007 |
| postgres | 5432 |
| redis | 6379 |

---

## Environment Variables

Copy `.env.example` to `.env` — defaults work out of the box with `docker-compose.yml`.

---

## Branching Rules

| Branch | Rule |
|---|---|
| `main` | PR + 1 owner approval + all 4 CI jobs green |
| Feature | `feat/<pod>/<ticket>` — e.g. `feat/nova/cm-001` |
| Bugfix | `fix/<pod>/<ticket>` |

Direct pushes to `main` are blocked for everyone, including admins.

---

## CI Jobs

1. **Format & Lint** — Ruff, jscpd, lockfile check
2. **Type Checking** — Pyright strict
3. **Security** — Vulture, Bandit, detect-secrets, pip-audit
4. **Tests** — Pytest 100% coverage, real Postgres + Redis containers

All 4 must pass before merge is allowed.

---

## Tech Stack

Python 3.12 · FastAPI · PostgreSQL 16 · Redis 7 · Alembic · WeasyPrint · React 18 (frontend placeholder)

---

## Git Workflow & Conflict Handling

### Daily workflow (do this every day before you start coding)

```bash
git checkout main
git pull origin main              # get latest main

git checkout feat/nova/cm-001     # go back to your branch
git rebase main                   # replay your commits on top of latest main
```

> **Why rebase and not merge?**
> Rebase keeps the commit history linear and clean. Merge creates an extra "merge commit" that clutters the log. Always rebase your feature branch onto main — never merge main into your feature branch.

---

### Scenario 1 — main was updated while you were working

Someone merged a PR and main moved forward. Before you open your own PR, sync up:

```bash
git fetch origin                  # download latest without applying
git rebase origin/main            # replay your commits on top

# If there are conflicts, Git will pause and tell you which files conflict.
# Fix them (see below), then:
git rebase --continue

# If you want to cancel and go back to before the rebase:
git rebase --abort
```

---

### Scenario 2 — resolving a conflict step by step

Git marks conflicts inside the file like this:

```
<<<<<<< HEAD  (your changes)
def calculate():
    return coverage * 0.40
=======
def calculate():
    return coverage * 0.45
>>>>>>> origin/main  (incoming changes)
```

**Steps:**
1. Open the file and decide which version to keep (or combine both).
2. Delete the `<<<<<<<`, `=======`, and `>>>>>>>` marker lines.
3. Save the file.
4. Stage it: `git add apps/resilience_scorer/calculator.py`
5. Continue the rebase: `git rebase --continue`
6. Repeat for each conflicted file.

Run `git status` at any point to see which files are still conflicted.

> **Tip:** VS Code, PyCharm, and most editors have a built-in conflict UI — look for "Accept Current", "Accept Incoming", or "Accept Both" buttons above each conflict block. This is faster than editing markers by hand.

---

### Scenario 3 — you need changes from a teammate's branch

Your branch needs something a teammate wrote in their branch before they merged it. Two options:

**Option A — Cherry-pick (take specific commits only)**
```bash
git log origin/feat/pulsar/ev-002 --oneline    # find the commit hash you want
git cherry-pick a1b2c3d                         # apply just that commit to your branch
```
If there's a conflict, resolve it (same steps as Scenario 2), then `git cherry-pick --continue`.

**Option B — Merge the other branch into yours (take everything)**
```bash
git fetch origin
git merge origin/feat/pulsar/ev-002    # merges all their changes into your branch
```
Resolve any conflicts, then `git add` the files and `git merge --continue`.

> Use cherry-pick when you only want one or two specific commits.
> Use merge when you want all of their changes.

---

### Scenario 4 — your PR is behind main and GitHub says "branch is out of date"

GitHub blocks merge when your branch is behind main (our branch protection rule requires it to be up to date). Fix it:

```bash
git fetch origin
git rebase origin/main        # sync up
# fix conflicts if any
git push --force-with-lease   # force push is safe here — use --force-with-lease, NOT --force
```

> `--force-with-lease` is safer than `--force`. It refuses to push if someone else pushed to your branch since your last fetch, preventing you from accidentally overwriting their work.

---

### Quick reference

| Situation | Command |
|---|---|
| Sync your branch with latest main | `git fetch origin && git rebase origin/main` |
| Conflict during rebase | Fix file → `git add <file>` → `git rebase --continue` |
| Cancel an ongoing rebase | `git rebase --abort` |
| Take one commit from another branch | `git cherry-pick <hash>` |
| Merge all changes from another branch | `git merge origin/<branch>` |
| Push after a rebase | `git push --force-with-lease` |
| See what's different from main | `git diff main...HEAD` |
| See all commits on your branch | `git log main..HEAD --oneline` |
---

# Pod 4 — Framework Templates: Docker Integration

This section documents the Dockerized setup for **Pod 4 — Framework Templates**. Pod 4 provides the **Framework Registry**: a catalog of compliance frameworks (NIST CSF, ISO 27001, ISO 27002, PCI DSS, GDPR, NIS2, HIPAA, SOC 2), their controls, and cross-framework control mappings (crosswalks), surfaced through the shared web dashboard.

After `docker compose build && docker compose up`, a reviewer can open the dashboard, select any of the 8 supported frameworks, and browse its controls and cross-framework equivalent controls — with no manual setup steps beyond bringing the stack up.

## Pod 4 Architecture / Services

| Service | Image / Build | Purpose | Port |
|---|---|---|---|
| `postgres` | `postgres:16-alpine` | Relational database (currently unused by Pod 4's data path — see Known Limitations) | `5432` (host-side mapped per `docker-compose.yml`, see below) |
| `redis` | `redis:7-alpine` | Cache/queue (reserved for future use) | `6379` |
| `framework_registry` | Built from `Dockerfile.framework_registry` | FastAPI backend serving frameworks, controls, and crosswalk data from bundled JSON definitions | `10006` |
| `frontend` | Built from `frontend/Dockerfile` | Next.js dashboard (integrated from the separate `Dashboard-frontend` repo), calls `framework_registry` over HTTP | `3000` |

**Data flow:** `framework_registry` reads static JSON definitions (`frameworks.json`, `controls.json`, `crosswalks.json`) at request time and exposes them via REST. The `frontend` calls `framework_registry` through internal Next.js API routes (e.g. `/api/frameworks/[id]/controls`), which proxy and reshape the data for the dashboard UI.

## Pod 4 Environment Variables

In addition to the project-wide vars above:

| Variable | Default | Used by | Notes |
|---|---|---|---|
| `FRAMEWORK_REGISTRY_URL` | `http://framework_registry:10006` | frontend | Internal Docker network URL — do not hardcode `localhost` |
| `PORT_FRAMEWORK_REGISTRY` | `10006` | framework_registry | |

## Accessing the Pod 4 Dashboard

Open **http://localhost:3000** and navigate to **Compliance → Framework Setup**. The Framework Registry API docs (Swagger UI) are available directly at **http://localhost:10006/docs**.

## How to Verify / Test Pod 4

1. **Containers up:** `docker compose ps` — `postgres`, `redis`, `framework_registry`, `frontend` all `Up`/`healthy`.
2. **API smoke test:**
   ```bash
   curl http://localhost:10006/health
   curl http://localhost:10006/frameworks
   ```
   Should return 8 frameworks (NIST CSF 2.0, ISO 27001, ISO 27002, PCI DSS, GDPR, NIS2, HIPAA, SOC 2).
3. **Dashboard — Frameworks tab:** confirms all 8 frameworks list with correct control counts.
4. **Dashboard — Controls tab:** select any framework (e.g. ISO 27002) and confirm controls load with Ref/Category/Priority/Status columns populated.
5. **Dashboard — Control Mapping tab:** select a framework (e.g. NIST CSF 2.0) and confirm equivalent-control mappings render (e.g. `GV.OC-03` → ISO 27001 A.5.31, ISO 27002 5.31).
6. **Dashboard — Evidence tab:** loads without error, but Evidence Req./Type/Source columns currently show `—` for all controls — see Known Limitations below.
7. **Clean-environment retest:**
   ```bash
   docker compose down -v
   docker compose build
   docker compose up -d
   ```
   Repeat steps 1–5 above; results should be identical.

## Pod 4 Troubleshooting

- **Port 5432 already in use:** if you run Postgres locally outside Docker, it commonly binds `5432`. Override the host-side port via `.env` if you see a conflict.
- **Frontend shows stale data after a code change:** the `frontend` service has **no dev bind-mount** — it is a self-contained image build. Any change to frontend source requires:
  ```bash
  docker compose build frontend
  docker compose up -d frontend
  ```
  A plain container restart (`docker compose restart frontend`) will **not** pick up source changes.
- **`psql: FATAL: role "postgres" does not exist`:** you're using the wrong DB credentials — the correct user/db/password for this stack is `assurance` / `assurance` / `assurance`, not the Postgres image's default `postgres` role.
- **`docker compose exec postgres psql ... \dt` shows no tables:** expected in the current setup — see Known Limitations below.
- **System Health panel shows "Report Engine: Degraded":** currently unexplained; tracked as a known issue (see GitHub Issues) rather than something to silently ignore.

## Pod 4 Known Limitations / Issues

1. **Evidence tab shows no data (`—` in all rows).** The frontend's Evidence view expects `evidenceRequired` / `evidenceType` / `evidenceSource` fields, but the Next.js API route (`/api/frameworks/[id]/controls/route.ts`) currently hardcodes these to `null`/`[]` for every control. Investigation traced this to a **cross-pod dependency**: the actual evidence data model belongs to Pod 2's `evidence_aggregator` service, which is a separate application in this monorepo and is **not included as a service in Pod 4's `docker-compose.yml`**. Filed as a GitHub Issue rather than fixed here, since building/wiring Pod 2's service is outside Pod 4's scope.
2. **`postgres` service is provisioned but not populated.** No Alembic migrations have been run (`alembic current` returns empty) and the `public` schema has zero tables. This is currently harmless because `framework_registry`'s actual data (frameworks, controls, crosswalks) is read from bundled JSON files, not the database — but it means the Postgres service and its persistent volume are effectively unused in Pod 4's current implementation.
3. **No dev bind-mount for the frontend.** The `frontend` service builds a self-contained image; there's no live-reload volume for local development inside Docker. This is intentional for a reproducible, production-style build, but means any source change requires a full `docker compose build frontend` — see Troubleshooting above.
4. **System Health panel reports "Report Engine: Degraded."** Cause not yet identified; filed as a GitHub Issue for follow-up. Does not currently block core Framework Registry functionality (Frameworks/Controls/Control Mapping all verified working).

### Previously found and fixed during this integration
- **Control Mapping tab bug (fixed):** originally showed "0 controls with mappings" for every framework, despite `crosswalks.json` containing 2,926 lines of real mapping data and the backend's `/controls/{control_id}/crosswalks` endpoint returning correct data when queried directly. Root cause: the frontend's `route.ts` hardcoded `equivalentControls: []` instead of calling the crosswalks endpoint per control. Fixed by fetching crosswalks per control (in parallel) and populating `equivalentControls` from the response. Verified working post-fix (e.g., NIST CSF 2.0 now shows 31 mapped controls).

## Pod 4 GitHub Issues Filed

- `#<TBD>` — Evidence tab shows no data: Pod 4's Docker Compose stack does not include Pod 2's `evidence_aggregator` service, so evidence fields are unpopulated.
- `#<TBD>` — System Health panel shows "Report Engine: Degraded" with no clear root cause identified yet.

*(Update issue numbers once created on GitHub.)*