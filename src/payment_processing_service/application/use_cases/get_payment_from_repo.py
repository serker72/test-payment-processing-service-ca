from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.uow import PaymentUnitOfWorkProtocol
from payment_processing_service.domain.entities.payment import PaymentEntity


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GetPaymentByIdFromRepoUseCase:
    """Сценарий получения платежа по ID из репозитория."""

    uow: PaymentUnitOfWorkProtocol
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, entity_id: str) -> PaymentDTO | None:
        """Выполняет сценарий получения платежа по ID из репозитория."""
        async with self.uow:
            payment_entity: PaymentEntity | None = await self.uow.repository.get_by_id(entity_id)
            if payment_entity:
                logger.info(f"Payment found in repository, entity_id={entity_id}")
                return self.payment_mapper.to_dto(payment_entity)
            logger.info(f"Payment not found in repository, entity_id={entity_id}")
            return None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GetPaymentByIdempotencyKeyFromRepoUseCase:
    """Сценарий получения платежа по idempotency_key из репозитория."""

    uow: PaymentUnitOfWorkProtocol
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, idempotency_key: str) -> PaymentDTO | None:
        """Выполняет сценарий получения платежа по idempotency_key из репозитория."""
        async with self.uow:
            payment_entity: PaymentEntity | None = await self.uow.repository.get_by_idempotency_key(idempotency_key)
            if payment_entity:
                logger.info(f"Payment found in repository, idempotency_key={idempotency_key}")
                return self.payment_mapper.to_dto(payment_entity)
            logger.info(f"Payment not found in repository, idempotency_key={idempotency_key}")
            return None
