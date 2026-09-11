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

## Docker Integration — Pod 2

This repository includes the Dockerized Evidence Aggregator implementation for Pod 2.

### Architecture

The Docker Compose stack contains:

| Service | Purpose | Container Port |
|---|---|---:|
| `postgres` | Persistent relational database | 5432 |
| `redis` | Redis service used by the Evidence Aggregator | 6379 |
| `db-migrate` | Runs Alembic database migrations | — |
| `db-seed` | Seeds initial framework/control data | — |
| `evidence-aggregator` | Evidence Aggregator API | 10002 |
| `dashboard` | Next.js Dashboard frontend | 3000 |

The Dashboard is maintained in the separate `Dashboard-frontend` repository and is expected to be checked out beside this repository:

```text
D:\CyBreach\
├── M3_Assurance\
└── Dashboard-frontend\
### Prerequisites

- Docker Desktop with Docker Compose
- M3_Assurance and Dashboard-frontend checked out as sibling directories

### Build and Start

From the M3_Assurance directory:

docker compose build
docker compose up -d
docker compose ps

### Endpoints

- Dashboard: http://localhost:3000
- Evidence Aggregator API: http://localhost:10002
- Swagger / OpenAPI: http://localhost:10002/docs
- Health: http://localhost:10002/health

### Evidence Aggregator API

- GET /evidence-links
- POST /evidence-links
- GET /evidence-summary/{engagement_id}

### Dashboard Integration

The Dashboard communicates with the Evidence Aggregator through the Docker Compose service network.

EVIDENCE_AGGREGATOR_URL=http://evidence-aggregator:10002

Dashboard proxy routes:

- /api/evidence/links
- /api/evidence/summary/{engagement_id}

### Verification

Run docker compose ps to verify service health.

Use docker compose logs evidence-aggregator to inspect aggregator logs.

Use docker compose logs dashboard to inspect dashboard logs.

The Evidence Aggregator health endpoint should report successful database and Redis connectivity.

### Stop the Stack

docker compose down

To remove the persistent PostgreSQL volume as well:

docker compose down -v

### Pod 2 Integration Test

The Dockerized Pod 2 implementation was verified with docker compose build and docker compose up -d.

Verified API workflow: GET /health, POST /evidence-links, GET /evidence-links, and GET /evidence-summary/{engagement_id}.

Dashboard-to-Evidence-Aggregator communication was verified through the Dashboard Next.js API proxy.
