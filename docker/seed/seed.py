"""Seed framework and control master data for Docker development."""

import asyncio
import json
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


ROOT = Path("/app")
FIXTURES = ROOT / "tests" / "fixtures"

DATABASE_URL = os.environ["DATABASE_URL"]


def load_fixture(filename: str) -> list[dict]:
    """Load JSON fixture data."""
    return json.loads((FIXTURES / filename).read_text())


async def main() -> None:
    """Seed frameworks and controls idempotently."""

    frameworks = load_fixture("frameworks.json")
    controls = load_fixture("controls.json")

    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        for framework in frameworks:
            await conn.execute(
                text(
                    """
                    INSERT INTO frameworks
                        (
                            framework_id,
                            name,
                            version,
                            description,
                            regions
                        )
                    VALUES
                        (
                            :fid,
                            :name,
                            :version,
                            :description,
                            :regions
                        )
                    ON CONFLICT (framework_id) DO NOTHING
                    """
                ),
                {
                    "fid": framework["framework_id"],
                    "name": framework["name"],
                    "version": framework["version"],
                    "description": framework["description"],
                    "regions": framework["regions"],
                },
            )

        for control in controls:
            await conn.execute(
                text(
                    """
                    INSERT INTO controls
                        (
                            control_id,
                            framework_id,
                            category,
                            name,
                            description,
                            attack_mapping
                        )
                    VALUES
                        (
                            :cid,
                            :fid,
                            :category,
                            :name,
                            :description,
                            :attack_mapping
                        )
                    ON CONFLICT (control_id) DO NOTHING
                    """
                ),
                {
                    "cid": control["control_id"],
                    "fid": control["framework_id"],
                    "category": control["category"],
                    "name": control["name"],
                    "description": control["description"],
                    "attack_mapping": control["attack_mapping"],
                },
            )

    await engine.dispose()

    print(f"Seed complete: {len(frameworks)} frameworks, {len(controls)} controls.")


if __name__ == "__main__":
    asyncio.run(main())
