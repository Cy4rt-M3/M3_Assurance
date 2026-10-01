"""
guard-my-code.py — Cross-platform quality gate. Mirrors CI exactly.
Works on Linux, macOS, Windows CMD, Windows PowerShell.
Usage: uv run python guard-my-code.py
"""

import os
import platform
import shutil
import subprocess
import sys

from apps.shared.settings import Settings


def _run(cmd: list[str], *, check: bool = True, **kw) -> int:
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, **kw)  # noqa: S603
    if result.returncode != 0 and check:
        print("\n❌  Failed — fix errors above and re-run.", file=sys.stderr)
        sys.exit(result.returncode)
    return result.returncode


def _step(label: str, cmd: list[str], *, check: bool = True) -> None:
    print(f"\n{label}")
    _run(cmd, check=check)


def _sync_deps() -> None:
    _step("📦 Syncing dependencies with uv...", ["uv", "sync", "--all-extras", "--dev"])


def _check_lockfile() -> None:
    _step("🔒 Checking uv lockfile is up-to-date...", ["uv", "lock", "--check"])


def _format() -> None:
    _step("🎨 Formatting code with ruff...", ["uv", "run", "ruff", "format"])


def _lint() -> None:
    _step(
        "🔍 Linting with ruff (McCabe complexity ≤4)...",
        ["uv", "run", "ruff", "check", "."],
    )


def _duplicates() -> None:
    print("\n🧩 Detecting duplicate code...")

    npx = "npx.cmd" if platform.system() == "Windows" else "npx"

    if shutil.which(npx):
        _run([npx, "jscpd", "."])
    else:
        print("  ⚠️  npx not found — skipping (install Node.js to enable)")


def _typecheck() -> None:
    _step("🧠 Type-checking with pyright...", ["uv", "run", "pyright"])


def _dead_code() -> None:
    _step(
        "🦅 Detecting dead code with vulture...",
        [
            "uv",
            "run",
            "python",
            "-m",
            "vulture",
            "--exclude",
            ".venv",
            ".",
            "--min-confidence",
            "100",
        ],
    )


def _security() -> None:
    _step(
        "🛡️  Security audit with bandit...",
        ["uv", "run", "bandit", "-r", "apps"],
    )


def _secrets() -> None:
    print("\n🔐 Checking for secrets in code...")
    result = subprocess.run(  # noqa: S603
        ["git", "ls-files"], capture_output=True, text=True, check=True
    )
    tracked = [f for f in result.stdout.splitlines() if f]
    if not tracked:
        return
    _run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "import sys; "
            "from detect_secrets.pre_commit_hook import main; "
            "sys.exit(main(sys.argv[1:]))",
            "--baseline",
            ".secrets.baseline",
            *tracked,
        ]
    )


def _audit_deps() -> None:
    _step(
        "🔎 Auditing dependencies for CVEs...",
        ["uv", "run", "python", "-m", "pip_audit", "."],
    )


def _migrate_test_db() -> None:
    settings = Settings()
    test_db_url = settings.database_test_url
    print("\n🗃️ Running migrations on test DB...")
    env = {**os.environ, "DATABASE_URL": test_db_url}
    _run(["uv", "run", "alembic", "upgrade", "head"], env=env)


def _tests() -> None:
    _step(
        "🧪 Running tests (real Postgres + Redis — no mocks)...",
        [
            "uv",
            "run",
            "pytest",
            "--cov=apps",
            "--cov-report=term-missing",
            "--cov-fail-under=100",
            "-x",
        ],
    )


def main() -> None:
    _sync_deps()
    _check_lockfile()
    _format()
    _lint()
    _duplicates()
    _typecheck()
    _dead_code()
    _security()
    _secrets()
    _audit_deps()
    _migrate_test_db()
    _tests()
    print("\n✅  All guards passed — safe to push.\n")


if __name__ == "__main__":
    main()
