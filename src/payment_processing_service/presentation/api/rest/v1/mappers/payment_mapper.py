from dataclasses import dataclass
from typing import final
from uuid import uuid4

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.presentation.api.rest.v1.schemas.common import PaymentMetaDataSchema
from payment_processing_service.presentation.api.rest.v1.schemas.requests import PaymentCreateRequestSchema
from payment_processing_service.presentation.api.rest.v1.schemas.responses import (
    PaymentCreateResponseSchema,
    PaymentResponseSchema,
)


@final
@dataclass(frozen=True, slots=True)
class PaymentPresentationMapper:
    """Mapper для конвертации между DTO приложений и схемами запросов/ответов API."""

    def from_request(self, data: PaymentCreateRequestSchema) -> PaymentDTO:
        """Преобразует схему запроса API в DTO приложения."""
        return PaymentDTO(
            id=uuid4(),
            amount=data.amount,
            currency=CurrencyDTO(value=data.currency),
            description=data.description,
            meta_data=PaymentMetaDataDTO(
                address=data.meta_data.address,
                fio=data.meta_data.fio,
                exp_date=data.meta_data.exp_date,
                bank=data.meta_data.bank,
                phone=data.meta_data.phone,
            ),
            status=PaymentStatusDTO(value=data.status),
            idempotency_key=data.idempotency_key,
            webhook_url=data.webhook_url,
            expired_at=data.expired_at,
        )

    def to_response(self, dto: PaymentDTO) -> PaymentResponseSchema:
        """Преобразует DTO приложения в схему ответа API."""
        return PaymentResponseSchema(
            id=dto.id,
            amount=dto.amount,
            currency=str(dto.currency.value),
            description=dto.description,
            meta_data=PaymentMetaDataSchema(
                address=dto.meta_data.address,
                fio=dto.meta_data.fio,
                exp_date=dto.meta_data.exp_date,
                bank=dto.meta_data.bank,
                phone=dto.meta_data.phone,
            ),
            status=str(dto.status.value),
            idempotency_key=dto.idempotency_key,
            webhook_url=dto.webhook_url,
            expired_at=dto.expired_at,
            processing_error_message=dto.processing_error_message,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    def to_create_response(self, dto: PaymentDTO) -> PaymentCreateResponseSchema:
        """Преобразует DTO приложения в схему ответа API."""
        return PaymentCreateResponseSchema(
            payment_id=str(dto.id),
            status=str(dto.status.value),
            created_at=dto.created_at,
        )
