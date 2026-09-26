# M3 Assurance

CyArt Tech LLP — Compliance, Evidence & Resilience Scoring Engine.

---
## Pod Nova — Docker Integration

This branch (`Docker_Integrated_PodNova`) provides a Dockerized setup for the M3 Assurance platform, including the Pod Nova backend services and the integrated frontend dashboard.

### Architecture

The Docker Compose setup runs five services:

| Service              | Purpose                        | Host Port |
| -------------------- | ------------------------------ | --------: |
| `postgres`           | PostgreSQL database            |    `5434` |
| `redis`              | Redis cache/service dependency |    `6380` |
| `framework_registry` | Framework Registry API         |   `10006` |
| `control_mapping`    | Control Mapping API            |   `10001` |
| `dashboard`          | Next.js frontend dashboard     |    `3000` |

The backend services use PostgreSQL and Redis through the Docker Compose network. The dashboard communicates with the backend APIs through the exposed localhost ports.

### Prerequisites

* Docker Desktop installed and running
* Git
* A free host port for `3000`, `10001`, `10006`, `5434`, and `6380`

### Environment Configuration

The Docker Compose setup provides default values for the PostgreSQL configuration:

```text
POSTGRES_USER=assurance
POSTGRES_PASSWORD=assurance
POSTGRES_DB=assurance
```

Backend containers use the Docker service names for internal communication:

```text
DATABASE_URL=postgresql+asyncpg://assurance:assurance@postgres:5432/assurance
REDIS_URL=redis://redis:6379/0
```

The dashboard uses:

```text
NEXT_PUBLIC_FRAMEWORK_API_URL=http://localhost:10006
NEXT_PUBLIC_MAPPING_API_URL=http://localhost:10001
```

No manual database or Redis installation is required when using Docker Compose.

### Build and Start

From the repository root:

```bash
docker compose build
docker compose up -d
```

Check the container status:

```bash
docker compose ps
```

All five services should be running, with PostgreSQL and Redis showing healthy status.

### Dashboard Access

Open the dashboard in a browser:

```text
http://localhost:3000
```

The dashboard retrieves framework and control data from the Framework Registry API and mapping data from the Control Mapping API.

### API Verification

Framework Registry health check:

```bash
curl http://localhost:10006/health
```

List available frameworks:

```bash
curl http://localhost:10006/frameworks
```

Test a control mapping:

```bash
curl "http://localhost:10001/mappings/gdpr:Article%2024"
```

A successful mapping request returns the mapped target control and equivalence level.

### Data Persistence

PostgreSQL data is stored in the Docker named volume:

```text
postgres_data
```

The database initialization script is mounted read-only from:

```text
docker/postgres/init.sql
```

Do not use `docker compose down -v` unless database volume deletion is intentionally required, because this removes the PostgreSQL Docker volume.

### Stopping the Services

To stop the complete Docker Compose environment:

```bash
docker compose down
```

To stop only the dashboard while keeping the backend services running:

```bash
docker stop m3_assurance-dashboard-1
```

The dashboard can then be started again with:

```bash
docker compose start dashboard
```

### Troubleshooting

#### Port 3000 already in use

If the dashboard cannot start because port `3000` is already occupied, stop the application using that port or stop the separate frontend development server before running the Docker dashboard.

Check the port with:

```bash
lsof -i :3000
```

#### Backend service unavailable

Check the service logs:

```bash
docker compose logs --tail=50 framework_registry
docker compose logs --tail=50 control_mapping
```

#### Dashboard logs

```bash
docker compose logs --tail=50 dashboard
```

#### Check service status

```bash
docker compose ps
```

### Verification Performed

The Docker integration was verified with:

* Successful `docker compose config` validation
* Successful `docker compose build`
* All five containers running
* PostgreSQL health check passing
* Redis health check passing
* Framework Registry `/health` returning successfully
* Framework Registry framework listing verified
* Control Mapping API verified with a GDPR control mapping
* Dashboard successfully loading at `http://localhost:3000`
* Framework and control data displayed in the dashboard
* Control mapping information displayed in the dashboard
* Container logs checked with no application errors observed

### Known Limitations

* The dashboard currently expects the backend APIs to be reachable through the host's localhost ports.
* Host ports `3000`, `10001`, `10006`, `5434`, and `6380` must be available.
* The Docker setup uses default development credentials for PostgreSQL and should use secure credentials for production deployments.
* The existing root project README also documents the non-Docker development and testing workflow; the Docker workflow above is intended for the integrated Pod Nova environment.

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