from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DECIMAL, DateTime, Enum, Index, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, registry

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum

mapper_registry = registry()


@mapper_registry.mapped
class PaymentModel:
    """Модель SQLAlchemy для таблицы платежей."""

    __tablename__ = "payments"
    __table_args__ = (Index("uq_payments_idempotency_key", "idempotency_key", unique=True),)

    def __init__(
        self,
        *,
        id: UUID,
        amount: Decimal,
        currency: CurrencyEnum,
        description: str,
        meta_data: dict[str, Any],
        status: PaymentStatusEnum,
        idempotency_key: str,
        webhook_url: str | None = None,
        expired_at: datetime | None = None,
        processing_error_message: str | None = None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """Инициализирует новый экземпляр PaymentModel."""
        self.id = id
        self.amount = amount
        self.currency = currency
        self.description = description
        self.meta_data = meta_data
        self.status = status
        self.idempotency_key = idempotency_key
        self.webhook_url = webhook_url
        self.expired_at = expired_at
        self.processing_error_message = processing_error_message
        self.created_at = created_at
        self.updated_at = updated_at

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    # currency: Mapped[str] = mapped_column(String(), nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(CurrencyEnum, name="type_payment_currencies"),
        nullable=False,
        default=CurrencyEnum.RUB,
    )
    description: Mapped[str] = mapped_column(String(), nullable=False)
    meta_data: Mapped[postgresql.JSONB] = mapped_column(postgresql.JSONB(none_as_null=True), nullable=False, default={})
    # status: Mapped[str] = mapped_column(String(), nullable=False)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum, name="type_payment_statuses"),
        nullable=False,
        default=PaymentStatusEnum.pending,
    )
    idempotency_key: Mapped[str] = mapped_column(String(), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(), nullable=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_error_message: Mapped[str] = mapped_column(String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """Возвращает строковое представление PaymentModel."""
        return (
            f"<PaymentModel(id={self.id!s}, currency={self.currency!r}, amount={self.amount!r}, "
            f"idempotency_key={self.idempotency_key!r})>"
        )
