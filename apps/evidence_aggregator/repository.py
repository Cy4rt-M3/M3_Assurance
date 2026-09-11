"""Database operations for the Evidence Aggregator service."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.evidence_aggregator.models import EvidenceLink


async def create_evidence_link(
    session: AsyncSession,
    link: EvidenceLink,
) -> EvidenceLink:
    """Persist one evidence link."""
    await session.execute(
        text(
            """
            INSERT INTO evidence_links
                (
                    link_id,
                    control_id,
                    verdict_id,
                    evidence_hash,
                    chain_position
                )
            VALUES
                (
                    :link_id,
                    :control_id,
                    :verdict_id,
                    :evidence_hash,
                    :chain_position
                )
            """
        ),
        link.model_dump(),
    )
    await session.commit()

    return link


async def get_evidence_links(
    session: AsyncSession,
    verdict_id: str | None = None,
    control_id: str | None = None,
) -> list[EvidenceLink]:
    """Return stored evidence links, optionally filtered."""

    query = """
        SELECT
            link_id,
            control_id,
            verdict_id,
            evidence_hash,
            chain_position
        FROM evidence_links
    """

    conditions: list[str] = []
    params: dict[str, str] = {}

    if verdict_id is not None:
        conditions.append("verdict_id = :verdict_id")
        params["verdict_id"] = verdict_id

    if control_id is not None:
        conditions.append("control_id = :control_id")
        params["control_id"] = control_id

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY chain_position ASC, created_at ASC"

    result = await session.execute(
        text(query),
        params,
    )

    return [
        EvidenceLink(
            link_id=row.link_id,
            control_id=row.control_id,
            verdict_id=row.verdict_id,
            evidence_hash=row.evidence_hash,
            chain_position=row.chain_position,
        )
        for row in result
    ]


async def get_evidence_summary(
    session: AsyncSession,
    engagement_id: str,
) -> tuple[int, int]:
    """Return total links and unique hashes for an engagement.

    EXISTS is used instead of a direct JOIN so duplicate control-status
    rows cannot cause the same evidence link to be counted multiple times.
    """

    result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_links,
                COUNT(DISTINCT el.evidence_hash) AS unique_hashes
            FROM evidence_links el
            WHERE EXISTS (
                SELECT 1
                FROM control_statuses cs
                WHERE cs.control_id = el.control_id
                  AND cs.engagement_id = :engagement_id
            )
            """
        ),
        {"engagement_id": engagement_id},
    )

    row = result.one()

    return int(row.total_links), int(row.unique_hashes)
