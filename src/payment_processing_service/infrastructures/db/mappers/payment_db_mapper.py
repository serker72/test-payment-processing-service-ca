from dataclasses import dataclass
from typing import final

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus
from payment_processing_service.infrastructures.db.models.payment import PaymentModel


@final
@dataclass(frozen=True, slots=True)
class PaymentDBMapper:
    """Mapper для конвертации между PaymentEntity (домен) и PaymentModel (SQLAlchemy)."""

    def to_entity(self, model: PaymentModel) -> PaymentEntity:
        """Преобразует SQLAlchemy PaymentModel в доменную PaymentEntity."""
        return PaymentEntity(
            id=model.id,
            amount=model.amount,
            currency=Currency(value=model.currency.value),
            description=model.description,
            meta_data=PaymentMetaData(
                address=model.meta_data["address"],
                fio=model.meta_data["fio"],
                exp_date=model.meta_data.get("exp_date"),
                bank=model.meta_data.get("bank"),
                phone=model.meta_data.get("phone"),
            ),
            status=PaymentStatus(value=model.status.value),
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            expired_at=model.expired_at,
            processing_error_message=model.processing_error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: PaymentEntity) -> PaymentModel:
        """Преобразует доменную PaymentEntity в SQLAlchemy PaymentModel."""
        return PaymentModel(
            id=entity.id,
            amount=entity.amount,
            currency=CurrencyEnum(entity.currency.value),
            description=entity.description,
            meta_data={
                "address": entity.meta_data.address,
                "fio": entity.meta_data.fio,
                "exp_date": entity.meta_data.exp_date,
                "bank": entity.meta_data.bank,
                "phone": entity.meta_data.phone,
            },
            status=PaymentStatusEnum(entity.status.value),
            idempotency_key=entity.idempotency_key,
            webhook_url=entity.webhook_url,
            expired_at=entity.expired_at,
            processing_error_message=entity.processing_error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def update_model_from_entity(self, model: PaymentModel, entity: PaymentEntity) -> None:
        """Обновляет существующую SQLAlchemy PaymentModel с помощью данных из доменной PaymentEntity."""
        model.amount = entity.amount
        model.currency = CurrencyEnum(entity.currency.value)
        model.description = entity.description
        model.meta_data = {
            "address": entity.meta_data.address,
            "fio": entity.meta_data.fio,
            "exp_date": entity.meta_data.exp_date,
            "bank": entity.meta_data.bank,
            "phone": entity.meta_data.phone,
        }
        model.status = PaymentStatusEnum(entity.status.value)
        model.idempotency_key = entity.idempotency_key
        model.webhook_url = entity.webhook_url
        model.expired_at = entity.expired_at
        model.processing_error_message = entity.processing_error_message
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at
