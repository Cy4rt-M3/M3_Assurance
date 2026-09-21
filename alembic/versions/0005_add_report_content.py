"""Store the rendered report payload (HTML or PDF bytes) on the row.

Previously only a content hash was persisted, so generated reports could
never be retrieved. Adding a nullable bytea column lets the download
endpoint return the actual artifact.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("content", sa.LargeBinary()))


def downgrade() -> None:
    op.drop_column("reports", "content")