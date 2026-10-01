# Build & Run — M3_Assurance

Quick on-ramp for new team members. The full ten-point setup (Python 3.12/uv-managed deps pinned by `uv.lock`, Postgres 16, Redis 7, 9 microservices, FFmpeg-less PDF/Hypercore-verified report pipeline) is captured in `README.md` and `master_setup.sh`; this file is the person-to-person quickstart.

## 1. Clone

```bash
git clone https://github.com/Cy4rt-M3/M3_Assurance.git
cd M3_Assurance
git checkout final            # primary integration branch; tag v_1 = current snapshot
```

## 2. Preflight

Requires **Docker** (for Postgres + Redis) and **uv**. Install uv if missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # or: pip install uv
```

### Python version

Primary validation environment: **Python 3.12.13** (the version pinned by the project). Validated results: 249 tests passing at 100% coverage, and `guard-my-code.py` passing end to end.

Fallback only: if Python 3.12 cannot be used on a machine (for example, its DLLs are blocked by the OS), Python 3.14 can be used as a workaround. Set `UV_PYTHON` to the 3.14 interpreter before running `uv sync`.

## 3. Environment

```bash
cp .env.example .env
```

**Do not copy real secrets into `.env`** unless you own the deployment. Defaults
use dummy creds (`assurance`/`assurance`, redis-in-DB) so a fresh checkout fails
safe. The CI gate (`guard-my-code.py`) rejects any attempt to commit a real
credential or a hash not on the `.secrets.baseline` allowlist.

## 4. Build

```bash
uv sync --all-groups --all-extras                      # creates .venv, exact versions from uv.lock (no drift)
docker compose up -d         # postgres:5432 (internal), redis:6379; healthchecks gate startup
uv run python master_setup.py  # runs alembic migrations + seeds framework/crosswalk definitions
```

## 5. Run the platform

Each service is an independent FastAPI app on its own port (see `run-metadata` /
`architecture.md` under the audit skill output, or `apps/*/README.md`):

```bash
uv run uvicorn apps.control_mapping.main:app       --port 10001 &
uv run uvicorn apps.evidence_aggregator.main:app   --port 10002 &
uv run uvicorn apps.gap_analyzer.main:app          --port 10003 &
uv run uvicorn apps.resilience_scorer.main:app     --port 10004 &
uv run uvicorn apps.report_generator.main:app      --port 10005 &
uv run uvicorn apps.framework_registry.main:app    --port 10006 &
uv run uvicorn apps.report_publisher.main:app      --port 10007 &
```
(Ports are declared once in `apps/shared/settings.py` — the values above are
those defaults; if yours differ, trust the settings file, not this doc.)

## 6. Verify

```bash
uv run python -m pytest                # full suite; requires postgres+redis up (no mocks, real deps)
uv run python guard-my-code.py      # ruff + pyright strict + bandit + detect-secrets + pip-audit, 100% coverage gate
for p in 10001 10002 10003 10004 10005 10006 10007; do
  curl -s http://127.0.0.1:$p/health | head -1; echo " <- $p"
done
```

## 7. Rebuild after pulling new work

```bash
git checkout final && git pull
uv sync --all-groups --all-extras                      # refresh exact pins
uv run python master_setup.py
docker compose up -d
```

## Windows notes

- Dev tools (pytest, ruff, pyright, bandit and so on) are installed as an extra. Use `uv sync --all-groups --all-extras`, otherwise `pytest` will be missing from `.venv`.
- Windows Application Control can block executables that `uv run` launches (os error 4551), for example `alembic.exe`, `vulture`, `detect-secrets-hook` and `pip-audit`. Launch them through Python instead: `uv run python -m alembic upgrade head`, `uv run python -m pip_audit .`, `uv run python -m uvicorn ...`. `guard-my-code.py` already does this.
- The duplicate-code check in `guard-my-code.py` is skipped when `npx` (Node.js) is not installed.

## Trust note

This platform **reviews and scores evidence that crosses an external trust
boundary** (verdicts, engagement data, OCSF events). The services have **no
authentication/authorization by design** — anyone who can reach a port can read
or write any engagement. Run it on an isolated network, bind to loopback for
evaluation, and add an authz layer in front before exposing on a shared
network. See `../security-audit-skill/M3_Assurance/run-1/` for the full audit
ledger and findings.
