"""Add engagements, verdicts and deliveries tables for the end-to-end pipeline.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_control_statuses_engagement_control",
        "control_statuses",
        ["engagement_id", "control_id"],
        unique=True,
    )
    op.create_table(
        "engagements",
        sa.Column("engagement_id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization", sa.String(255), nullable=False),
        sa.Column(
            "frameworks", sa.ARRAY(sa.String(64)), nullable=False, server_default="{}"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "verdicts",
        sa.Column("verdict_id", sa.String(64), primary_key=True),
        sa.Column("engagement_id", sa.String(64), nullable=False),
        sa.Column("technique_id", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("severity_id", sa.SmallInteger, nullable=False),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_verdicts_engagement", "verdicts", ["engagement_id"])
    op.create_index("ix_verdicts_technique", "verdicts", ["technique_id"])

    op.create_table(
        "deliveries",
        sa.Column("delivery_id", sa.String(64), primary_key=True),
        sa.Column("report_id", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "delivered_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_deliveries_report", "deliveries", ["report_id"])


def downgrade() -> None:
    op.drop_table("deliveries")
    op.drop_table("verdicts")
    op.drop_table("engagements")
