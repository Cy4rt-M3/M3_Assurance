"""Database operations for the Report Generator service."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.report_generator.models import Report


async def save_report(
    session: AsyncSession,
    report: Report,
    content: bytes | None = None,
) -> Report:
    """Persist one report row, optionally with its rendered payload."""
    await session.execute(
        text(
            """
            INSERT INTO reports
                (
                    report_id,
                    engagement_id,
                    framework_ids,
                    score,
                    format,
                    content_hash,
                    content
                )
            VALUES
                (
                    :report_id,
                    :engagement_id,
                    :framework_ids,
                    :score,
                    :format,
                    :content_hash,
                    :content
                )
            """
        ),
        {
            "report_id": report.report_id,
            "engagement_id": report.engagement_id,
            "framework_ids": report.framework_ids,
            "score": report.composite_score,
            "format": report.format,
            "content_hash": report.content_hash,
            "content": content,
        },
    )
    await session.commit()
    return report


async def get_report(
    session: AsyncSession,
    report_id: str,
) -> Report | None:
    """Return one report row, or None when missing."""
    result = await session.execute(
        text(
            """
            SELECT
                report_id,
                engagement_id,
                framework_ids,
                score,
                format,
                content_hash
            FROM reports
            WHERE report_id = :report_id
            """
        ),
        {"report_id": report_id},
    )
    row = result.one_or_none()
    if row is None:
        return None
    return Report(
        report_id=row.report_id,
        engagement_id=row.engagement_id,
        framework_ids=list(row.framework_ids),
        composite_score=float(row.score),
        format=row.format,
        content_hash=row.content_hash,
    )


async def list_reports(
    session: AsyncSession,
    engagement_id: str,
) -> list[Report]:
    """Return all stored reports for an engagement, newest first."""
    result = await session.execute(
        text(
            """
            SELECT
                report_id,
                engagement_id,
                framework_ids,
                score,
                format,
                content_hash
            FROM reports
            WHERE engagement_id = :engagement_id
            ORDER BY created_at DESC
            """
        ),
        {"engagement_id": engagement_id},
    )

    return [
        Report(
            report_id=row.report_id,
            engagement_id=row.engagement_id,
            framework_ids=list(row.framework_ids),
            composite_score=float(row.score),
            format=row.format,
            content_hash=row.content_hash,
        )
        for row in result
    ]


async def get_report_content(
    session: AsyncSession,
    report_id: str,
) -> tuple[str, bytes] | None:
    """Return the (format, payload) of one stored report, or None."""
    result = await session.execute(
        text(
            """
            SELECT format, content
            FROM reports
            WHERE report_id = :report_id
            """
        ),
        {"report_id": report_id},
    )
    row = result.one_or_none()
    if row is None or row.content is None:
        return None
    return row.format, row.content
