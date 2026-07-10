from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, final
from uuid import UUID

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CurrencyDTO:
    """Объект передачи данных валюты."""

    value: Literal[CurrencyEnum.RUB, CurrencyEnum.USD, CurrencyEnum.EUR]


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentStatusDTO:
    """Объект передачи данных статуса платежа."""

    value: Literal[PaymentStatusEnum.pending, PaymentStatusEnum.succeeded, PaymentStatusEnum.failed]


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class PaymentMetaDataDTO:
    address: str
    fio: str
    exp_date: str | None = None
    bank: str | None = None
    phone: str | None = None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentDTO:
    """Объект передачи данных платежа между слоями."""

    id: UUID
    amount: Decimal
    currency: CurrencyDTO
    description: str
    meta_data: PaymentMetaDataDTO
    status: PaymentStatusDTO
    idempotency_key: str
    webhook_url: str | None = None
    expired_at: datetime | None = None
    processing_error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentCreateNotificationDTO:
    """Объект передачи данных о создании платежа для уведомлений."""

    payment_id: UUID
    status: PaymentStatusDTO
    created_at: datetime
