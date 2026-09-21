"""Database operations for the Control Mapping service."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.framework_registry.models import Control
from apps.shared.attack_tactics import effective_mapping, labels_for


async def list_controls_for_techniques(
    session: AsyncSession,
    technique_ids: list[str],
    framework_ids: list[str],
) -> list[Control]:
    """Return controls whose attack mapping covers any of the techniques."""
    labels = sorted({label for tid in technique_ids for label in labels_for(tid)})
    result = await session.execute(
        text(
            """
            SELECT control_id, framework_id, category, name, description, attack_mapping
            FROM controls
            WHERE CAST(framework_id AS text) = ANY(CAST(:framework_ids AS text[]))
              AND CAST(attack_mapping AS text[]) && CAST(:labels AS text[])
            """
        ),
        {
            "framework_ids": framework_ids,
            "labels": labels,
        },
    )

    return [
        Control(
            control_id=row.control_id,
            framework_id=row.framework_id,
            category=row.category,
            name=row.name,
            description=row.description,
            attack_mapping=list(row.attack_mapping),
        )
        for row in result
    ]


async def upsert_control_statuses(
    session: AsyncSession,
    engagement_id: str,
    statuses: dict[str, str],
    evidence_hashes: dict[str, str | None],
) -> None:
    """Insert or update one control status row per control."""
    for control_id, status in statuses.items():
        await session.execute(
            text(
                """
                INSERT INTO control_statuses
                    (engagement_id, control_id, status, evidence_hash, last_updated)
                VALUES (:engagement_id, :control_id, :status, :evidence_hash, now())
                ON CONFLICT (engagement_id, control_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    evidence_hash = EXCLUDED.evidence_hash,
                    last_updated = now()
                """
            ),
            {
                "engagement_id": engagement_id,
                "control_id": control_id,
                "status": status,
                "evidence_hash": evidence_hashes.get(control_id),
            },
        )
    await session.commit()


async def get_control_statuses(
    session: AsyncSession,
    engagement_id: str,
) -> dict[str, str]:
    """Return the control status map for an engagement."""
    result = await session.execute(
        text(
            """
            SELECT control_id, status
            FROM control_statuses
            WHERE engagement_id = :engagement_id
            """
        ),
        {"engagement_id": engagement_id},
    )
    return {row.control_id: row.status for row in result}


async def list_controls_by_id(
    session: AsyncSession,
    control_ids: list[str],
) -> list[Control]:
    """Return full controls rows for a set of control ids."""
    result = await session.execute(
        text(
            """
            SELECT control_id, framework_id, category, name, description, attack_mapping
            FROM controls
            WHERE CAST(control_id AS text) = ANY(CAST(:control_ids AS text[]))
            """
        ),
        {"control_ids": control_ids},
    )

    return [
        Control(
            control_id=row.control_id,
            framework_id=row.framework_id,
            category=row.category,
            name=row.name,
            description=row.description,
            attack_mapping=list(row.attack_mapping),
        )
        for row in result
    ]


def evidence_hash_map(
    statuses: dict[str, str],
    verdicts: list[dict[str, Any]],
    controls: list[Control],
) -> dict[str, str | None]:
    """Build a control_id → evidence hash map for controls with a Detected verdict."""
    tested = {v["technique_id"] for v in verdicts}
    map_by_control: dict[str, str | None] = {}
    for control in controls:
        effective = effective_mapping(control.attack_mapping, tested)
        hashes = [
            v["evidence_hash"]
            for v in verdicts
            if v["technique_id"] in effective and v["outcome"] == "Detected"
        ]
        control_id = control.control_id
        if control_id in statuses:
            select = statuses[control_id]
            map_by_control[control_id] = hashes[0] if hashes else None
            if select == "Not Met" and map_by_control[control_id] is None:
                map_by_control[control_id] = evidence_hash_for_control(
                    control, verdicts
                )
    return map_by_control


def evidence_hash_for_control(
    control: Control,
    verdicts: list[dict[str, Any]],
) -> str | None:
    """Return the first verdict evidence hash mapped to the control."""
    tested = {v["technique_id"] for v in verdicts}
    effective = effective_mapping(control.attack_mapping, tested)
    for verdict in verdicts:
        if verdict["technique_id"] in effective:
            return verdict["evidence_hash"]
    return None
