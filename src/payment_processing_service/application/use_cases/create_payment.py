from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.use_cases.get_payment_from_repo import (
    GetPaymentByIdempotencyKeyFromRepoUseCase,
    GetPaymentByIdFromRepoUseCase,
)
from payment_processing_service.application.use_cases.publish_payment_to_broker import PublishPaymentToBrokerUseCase
from payment_processing_service.application.use_cases.save_payment_to_repo import SavePaymentToRepoUseCase


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CreatePaymentUseCase:
    """Сценарий создания платежа, включаю сохранение в репозиторий, публикацию уведомления в брокере сообщений."""

    get_payment_by_id_from_repo_use_case: GetPaymentByIdFromRepoUseCase
    get_payment_by_idempotency_key_from_repo_use_case: GetPaymentByIdempotencyKeyFromRepoUseCase
    save_payment_to_repo_use_case: SavePaymentToRepoUseCase
    publish_payment_to_broker_use_case: PublishPaymentToBrokerUseCase

    async def __call__(self, payment_dto: PaymentDTO) -> PaymentDTO | None:
        """Выполняет сценарий создания платежа."""
        exist_payment_dto = await self.get_payment_by_idempotency_key_from_repo_use_case(
            str(payment_dto.idempotency_key)
        )
        if exist_payment_dto:
            logger.info(f"Payment found, idempotency_key={payment_dto.idempotency_key}")
            return exist_payment_dto

        await self.save_payment_to_repo_use_case(payment_dto)

        try:
            await self.publish_payment_to_broker_use_case(payment_dto)
        except:
            logger.warning(
                f"Failed to publish payment notification to message broker (non-critical), id={payment_dto.id}"
            )

        logger.info(f"Payment successfully created, id={payment_dto.id}")
        return await self.get_payment_by_id_from_repo_use_case(str(payment_dto.id))
