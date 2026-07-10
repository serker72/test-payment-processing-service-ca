from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import final
from uuid import UUID, uuid4

from payment_processing_service.domain.entities.base import BaseEntity
from payment_processing_service.domain.exceptions import DomainValidationError
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class PaymentMetaData:
    address: str
    fio: str
    exp_date: str | None = None
    bank: str | None = None
    phone: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class PaymentEntity(BaseEntity):
    """Сущность платеж."""

    id: UUID = field(default_factory=uuid4)
    amount: Decimal
    currency: Currency
    description: str
    meta_data: PaymentMetaData
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str | None = None
    expired_at: datetime | None = None
    processing_error_message: str | None = None

    def __post_init__(self) -> None:
        """Проверяет бизнес-инварианты сущности платеж."""
        if self.amount <= Decimal(0):
            raise DomainValidationError("Amount must be greater than 0")
