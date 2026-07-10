from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.uow import PaymentUnitOfWorkProtocol


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SavePaymentToRepoUseCase:
    """Сценарий сохранения платежа в репозиторий."""

    uow: PaymentUnitOfWorkProtocol
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, payment_dto: PaymentDTO) -> None:
        """Выполняет сценарий сохранения платежа в репозиторий."""
        async with self.uow:
            payment_entity = self.payment_mapper.to_entity(payment_dto)
            await self.uow.repository.save(payment_entity)
        logger.info(f"Payment saved to repository, id={payment_dto.id}")
