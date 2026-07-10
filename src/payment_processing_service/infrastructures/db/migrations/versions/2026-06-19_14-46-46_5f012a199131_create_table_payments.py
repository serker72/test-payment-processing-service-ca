"""create table payments

Revision ID: 5f012a199131
Revises:
Create Date: 2026-06-19 14:46:46.255257

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum

# revision identifiers, used by Alembic.
revision: str = "5f012a199131"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "payments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            comment="ID платежа",
        ),
        sa.Column("amount", sa.DECIMAL(16, 2), nullable=False, comment="Сумма"),
        sa.Column(
            "currency",
            sa.Enum(*[item.name for item in iter(CurrencyEnum)], name="type_payment_currencies"),
            nullable=False,
            server_default=sa.text(f"'{CurrencyEnum.RUB.name}'"),
            comment="Валюта",
        ),
        sa.Column("description", sa.String(), nullable=False, comment="Описание"),
        sa.Column(
            "meta_data", postgresql.JSONB(none_as_null=True), nullable=False, server_default="{}", comment="Метаданные"
        ),
        sa.Column(
            "status",
            sa.Enum(*[item.name for item in iter(PaymentStatusEnum)], name="type_payment_statuses"),
            nullable=False,
            server_default=sa.text(f"'{PaymentStatusEnum.pending.name}'"),
            comment="Статус",
        ),
        sa.Column("idempotency_key", sa.String(), nullable=False, comment="Уникальный ключ для защиты от дублей"),
        sa.Column("webhook_url", sa.String(), nullable=True, comment="URL для отправки вебхука"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Время создания",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, comment="Время изменения"),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True, comment="Срок действия"),
        sa.Column("processing_error_message", sa.String(), nullable=True, comment="Сообщение об ошибке обработки"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        comment="Список платежей",
    )

    op.create_index(
        op.f("uq_payments_idempotency_key"),
        "payments",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("payments")
    op.execute("DROP TYPE IF EXISTS type_payment_currencies")
    op.execute("DROP TYPE IF EXISTS type_payment_statuses")
