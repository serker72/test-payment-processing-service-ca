"""create table outbox

Revision ID: 3da05cce5307
Revises: 5f012a199131
Create Date: 2026-06-20 13:11:09.186590

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3da05cce5307"
down_revision: Union[str, Sequence[str], None] = "5f012a199131"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "outbox",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("queue", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column("headers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attempts_count", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("deliveries_count", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("first_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acquired_token", sa.Uuid(), nullable=True),
        sa.Column("timer_id", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "outbox_lease_idx",
        "outbox",
        ["queue", "acquired_at"],
        unique=False,
        postgresql_where=sa.text("acquired_token IS NOT NULL"),
    )
    op.create_index(
        "outbox_pending_idx",
        "outbox",
        ["queue", "next_attempt_at"],
        unique=False,
        postgresql_where=sa.text("acquired_token IS NULL"),
    )
    op.create_index(
        "outbox_timer_id_uq",
        "outbox",
        ["queue", "timer_id"],
        unique=True,
        postgresql_where=sa.text("timer_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("outbox")
