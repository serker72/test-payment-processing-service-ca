from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.interfaces.uow import PaymentUnitOfWorkProtocol
from payment_processing_service.application.use_cases.execute_payment import ExecutePaymentUseCase
from payment_processing_service.application.use_cases.get_payment_from_repo import GetPaymentByIdFromRepoUseCase
from payment_processing_service.application.use_cases.save_payment_to_repo import SavePaymentToRepoUseCase
from payment_processing_service.application.use_cases.send_payment_webhook import SendPaymentWebhookUseCase
from payment_processing_service.config.enums import PaymentStatusEnum


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessPaymentUseCase:
    """Сценарий обработки платежа."""

    uow: PaymentUnitOfWorkProtocol
    get_payment_by_id_from_repo_use_case: GetPaymentByIdFromRepoUseCase
    execute_payment_use_case: ExecutePaymentUseCase
    save_payment_to_repo_use_case: SavePaymentToRepoUseCase
    send_payment_webhook_use_case: SendPaymentWebhookUseCase

    async def __call__(self, data: dict) -> bool:
        """Выполняет сценарий обработки платежа."""
        result = True
        async with self.uow:
            payment_dto: PaymentDTO | None = await self.get_payment_by_id_from_repo_use_case(data.get("payment_id"))
            if payment_dto and payment_dto.status.value == PaymentStatusEnum.pending.value:
                updated_payment_dto: PaymentDTO = await self.execute_payment_use_case(payment_dto)
                await self.save_payment_to_repo_use_case(updated_payment_dto)
                if payment_dto.webhook_url:
                    result = await self.send_payment_webhook_use_case(updated_payment_dto)

                logger.info(f"Payment successfully processed, id={payment_dto.id}")

            return result
