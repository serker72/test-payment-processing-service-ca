from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import final
from uuid import UUID

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.interfaces.serialization import PaymentSerializationMapperProtocol


@final
@dataclass(frozen=True, slots=True)
class InfrastructurePaymentMapper(PaymentSerializationMapperProtocol):
    """Mapper для преобразования DTO приложений в словари для внешних систем."""

    def to_dict(self, dto: PaymentDTO) -> dict:
        """Преобразует PaymentDTO в словарь для сериализации JSON."""
        return {
            "id": str(dto.id),
            "amount": float(dto.amount),
            "currency": {"value": dto.currency.value},
            "description": dto.description,
            "meta_data": {
                "address": dto.meta_data.address,
                "fio": dto.meta_data.fio,
                "exp_date": dto.meta_data.exp_date,
                "bank": dto.meta_data.bank,
                "phone": dto.meta_data.phone,
            },
            "status": {"value": dto.status.value},
            "idempotency_key": dto.idempotency_key,
            "webhook_url": dto.webhook_url,
            "expired_at": dto.expired_at and dto.expired_at.isoformat(),
            "processing_error_message": dto.processing_error_message,
            "created_at": dto.created_at.isoformat(),
            "updated_at": dto.updated_at.isoformat(),
        }

    def from_dict(self, data: dict) -> PaymentDTO:
        """Преобразует словарь из десериализации JSON в PaymentDTO."""
        return PaymentDTO(
            id=UUID(data["id"]),
            amount=Decimal(data["amount"]),
            currency=CurrencyDTO(value=data["currency"]["value"]),
            description=data["description"],
            meta_data=PaymentMetaDataDTO(
                address=data["meta_data"]["address"],
                fio=data["meta_data"]["fio"],
                exp_date=data["meta_data"].get("exp_date"),
                bank=data["meta_data"].get("bank"),
                phone=data["meta_data"].get("phone"),
            ),
            status=PaymentStatusDTO(value=data["status"]["value"]),
            idempotency_key=data["idempotency_key"],
            webhook_url=data.get("webhook_url"),
            expired_at=datetime.fromisoformat(data["expired_at"]),
            processing_error_message=data.get("processing_error_message"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def to_notification_dict(self, dto: PaymentCreateNotificationDTO) -> dict:
        """Преобразует PaymentCreateNotificationDTO в словарь для коммуникации с помощью брокера сообщений."""
        return {
            "payment_id": str(dto.payment_id),
            "status": {"value": dto.status.value},
            "created_at": dto.created_at.isoformat(),
        }
