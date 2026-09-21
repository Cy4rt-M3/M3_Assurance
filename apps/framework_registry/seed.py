"""Seed the registry definitions into the database. Complexity ≤4 guaranteed."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.framework_registry import loader
from apps.shared.settings import Settings


async def seed(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[int, int]:
    """Load frameworks and controls from the registry JSON into the database."""
    frameworks = loader.load_frameworks()
    controls = loader.load_controls()

    async with session_factory() as session:
        for framework in frameworks:
            await session.execute(
                text(
                    """
                    INSERT INTO frameworks
                        (framework_id, name, version, description, regions)
                    VALUES (:framework_id, :name, :version, :description, :regions)
                    ON CONFLICT (framework_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        version = EXCLUDED.version,
                        description = EXCLUDED.description,
                        regions = EXCLUDED.regions
                    """
                ),
                {
                    "framework_id": framework.framework_id,
                    "name": framework.name,
                    "version": framework.version,
                    "description": framework.description,
                    "regions": framework.regions,
                },
            )

        for control in controls:
            await session.execute(
                text(
                    """
                    INSERT INTO controls (
                        control_id, framework_id, category, name,
                        description, attack_mapping
                    )
                    VALUES
                        (
                            :control_id, :framework_id, :category, :name, :description,
                            :attack_mapping
                        )
                    ON CONFLICT (control_id) DO UPDATE SET
                        framework_id = EXCLUDED.framework_id,
                        category = EXCLUDED.category,
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        attack_mapping = EXCLUDED.attack_mapping
                    """
                ),
                {
                    "control_id": control.control_id,
                    "framework_id": control.framework_id,
                    "category": control.category,
                    "name": control.name,
                    "description": control.description,
                    "attack_mapping": list(control.attack_mapping),
                },
            )

        await session.commit()

    return len(frameworks), len(controls)


def build_session_factory_from_settings() -> async_sessionmaker[AsyncSession]:
    """Build an async session factory from the configured database URL."""
    engine = create_async_engine(Settings().database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def main() -> None:
    """Seed the registered frameworks and controls into the database."""
    factory = build_session_factory_from_settings()
    frameworks, controls = await seed(factory)
    print(f"[framework-registry] seeded {frameworks} frameworks, {controls} controls")


if __name__ == "__main__":
    asyncio.run(main())
