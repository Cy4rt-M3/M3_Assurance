"""Widen identifier and version columns past their previous limits.

HIPAA's version string ("Security Rule 45 CFR Part 164 Subpart C", 39 chars)
exceeds VARCHAR(32), and generated ids such as "ENG-…-vrd-0001" or
"<control_id>:<verdict_id>" can exceed VARCHAR(64).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "frameworks", "version", existing_type=sa.String(32), type_=sa.String(128)
    )
    op.alter_column(
        "verdicts", "verdict_id", existing_type=sa.String(64), type_=sa.String(128)
    )
    op.alter_column(
        "deliveries", "delivery_id", existing_type=sa.String(64), type_=sa.String(128)
    )
    op.alter_column(
        "reports", "report_id", existing_type=sa.String(64), type_=sa.String(128)
    )
    op.alter_column(
        "gap_analyses", "analysis_id", existing_type=sa.String(64), type_=sa.String(128)
    )
    op.alter_column(
        "resilience_scores",
        "score_id",
        existing_type=sa.String(64),
        type_=sa.String(128),
    )
    op.alter_column(
        "evidence_links", "link_id", existing_type=sa.String(64), type_=sa.String(196)
    )


def downgrade() -> None:
    op.alter_column(
        "evidence_links", "link_id", existing_type=sa.String(196), type_=sa.String(64)
    )
    op.alter_column(
        "resilience_scores",
        "score_id",
        existing_type=sa.String(128),
        type_=sa.String(64),
    )
    op.alter_column(
        "gap_analyses", "analysis_id", existing_type=sa.String(128), type_=sa.String(64)
    )
    op.alter_column(
        "reports", "report_id", existing_type=sa.String(128), type_=sa.String(64)
    )
    op.alter_column(
        "deliveries", "delivery_id", existing_type=sa.String(128), type_=sa.String(64)
    )
    op.alter_column(
        "verdicts", "verdict_id", existing_type=sa.String(128), type_=sa.String(64)
    )
    op.alter_column(
        "frameworks", "version", existing_type=sa.String(128), type_=sa.String(32)
    )
