"""Database operations for the Gap Analyzer service."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gap_analyzer.models import GapAnalysis


async def save_gaps(
    session: AsyncSession,
    gaps: list[GapAnalysis],
) -> list[GapAnalysis]:
    """Persist one row per gap, skipping rows that already exist."""
    for gap in gaps:
        await session.execute(
            text(
                """
                INSERT INTO gap_analyses (
                    analysis_id, engagement_id, control_id,
                    gap_type, priority, remediation
                )
                VALUES
                    (
                        :analysis_id, :engagement_id, :control_id, :gap_type, :priority,
                        :remediation
                    )
                ON CONFLICT (analysis_id) DO NOTHING
                """
            ),
            gap.model_dump(),
        )
    await session.commit()
    return gaps


async def list_gaps(
    session: AsyncSession,
    engagement_id: str,
) -> list[GapAnalysis]:
    """Return all gaps for an engagement, most critical first."""
    result = await session.execute(
        text(
            """
            SELECT
                analysis_id,
                engagement_id,
                control_id,
                gap_type,
                priority,
                remediation
            FROM gap_analyses
            WHERE engagement_id = :engagement_id
            ORDER BY priority ASC, created_at ASC
            """
        ),
        {"engagement_id": engagement_id},
    )

    return [
        GapAnalysis(
            analysis_id=row.analysis_id,
            engagement_id=row.engagement_id,
            control_id=row.control_id,
            gap_type=row.gap_type,
            priority=row.priority,
            remediation=row.remediation,
        )
        for row in result
    ]
