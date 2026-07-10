from dataclasses import dataclass
from typing import final

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


@final
@dataclass(frozen=True, slots=True)
class PaymentMapper(DtoPaymentEntityMapperProtocol):
    """Mapper для преобразования между доменными сущностями и DTO приложений."""

    def to_dto(self, entity: PaymentEntity) -> PaymentDTO:
        """Преобразует доменную сущность в объект передачи данных."""
        return PaymentDTO(
            id=entity.id,
            amount=entity.amount,
            currency=CurrencyDTO(value=entity.currency.value),
            description=entity.description,
            meta_data=PaymentMetaDataDTO(
                address=entity.meta_data.address,
                fio=entity.meta_data.fio,
                exp_date=entity.meta_data.exp_date,
                bank=entity.meta_data.bank,
                phone=entity.meta_data.phone,
            ),
            status=PaymentStatusDTO(value=entity.status.value),
            idempotency_key=entity.idempotency_key,
            webhook_url=entity.webhook_url,
            expired_at=entity.expired_at,
            processing_error_message=entity.processing_error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, dto: PaymentDTO) -> PaymentEntity:
        """Преобразует объект передачи данных в доменную сущность."""
        return PaymentEntity(
            id=dto.id,
            amount=dto.amount,
            currency=Currency(value=dto.currency.value),
            description=dto.description,
            meta_data=PaymentMetaData(
                address=dto.meta_data.address,
                fio=dto.meta_data.fio,
                exp_date=dto.meta_data.exp_date,
                bank=dto.meta_data.bank,
                phone=dto.meta_data.phone,
            ),
            status=PaymentStatus(value=dto.status.value),
            idempotency_key=dto.idempotency_key,
            webhook_url=dto.webhook_url,
            expired_at=dto.expired_at,
            processing_error_message=dto.processing_error_message,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def to_notification_dto(self, entity: PaymentEntity) -> PaymentCreateNotificationDTO:
        """Преобразует доменную сущность в объект передачи данных для уведомлений."""
        return PaymentCreateNotificationDTO(
            payment_id=entity.id,
            status=PaymentStatusDTO(value=entity.status.value),
            created_at=entity.created_at,
        )
