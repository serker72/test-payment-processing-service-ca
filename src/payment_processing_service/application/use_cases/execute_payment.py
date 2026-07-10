import asyncio
import random
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO, PaymentStatusDTO
from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.config.settings import Settings


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutePaymentUseCase:
    """Сценарий исполнения платежа."""

    settings: Settings

    async def __call__(self, payment_dto: PaymentDTO) -> PaymentDTO:
        """Выполняет сценарий исполнения платежа."""
        error_messages = [
            "Insufficient funds",
            "Incorrect card/wallet number",
            "Payment declined by the bank",
            "Suspected fraud",
            "Processing time expired",
        ]

        dt = datetime.now(timezone.utc)

        delay = random.uniform(self.settings.app.backend_payment_min_delay, self.settings.app.backend_payment_max_delay)
        await asyncio.sleep(delay)

        if payment_dto.expired_at and payment_dto.expired_at < dt:
            status = PaymentStatusEnum.failed.name
            processing_error_message = error_messages[-1]
        elif random.random() >= self.settings.app.backend_payment_success_rate:
            processing_error_message = random.choice(error_messages)
            status = PaymentStatusEnum.failed.name
        else:
            status = PaymentStatusEnum.succeeded
            processing_error_message = None

        updated_payment_dto = replace(
            payment_dto,
            status=PaymentStatusDTO(value=status),
            processing_error_message=processing_error_message,
            updated_at=dt,
        )
        logger.info(f"Payment executed, id={payment_dto.id}, status={status}")
        return updated_payment_dto
