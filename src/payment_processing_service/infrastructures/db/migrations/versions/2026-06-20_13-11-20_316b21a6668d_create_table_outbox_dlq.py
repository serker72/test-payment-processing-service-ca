"""create table outbox_dlq

Revision ID: 316b21a6668d
Revises: 3da05cce5307
Create Date: 2026-06-20 13:11:20.418839

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "316b21a6668d"
down_revision: Union[str, Sequence[str], None] = "3da05cce5307"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "outbox_dlq",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("original_id", sa.BigInteger(), nullable=False),
        sa.Column("queue", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("deliveries_count", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("failure_reason", sa.String(length=64), nullable=False),
        sa.Column("last_exception", sa.String(), nullable=True),
        sa.Column("timer_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("outbox_dlq_queue_failed_idx", "outbox_dlq", ["queue", "failed_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("outbox_dlq")
