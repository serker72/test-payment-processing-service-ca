from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.webhooks import SendPaymentWebhookProtocol
from payment_processing_service.domain.exceptions import WebhookDeliveryError


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SendPaymentWebhookUseCase:
    """Сценарий отправки вебхука для платежа."""

    http_client: SendPaymentWebhookProtocol
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, payment_dto: PaymentDTO) -> bool:
        """Выполняет сценарий отправки вебхука для платежа."""
        try:
            await self.http_client.send_webhook(payment_dto)
            logger.info(f"Webhook for payment send successful, id={payment_dto.id}, url={payment_dto.webhook_url}")
            return True
        # except WebhookDeliveryError as e:
        except Exception as e:
            logger.exception(
                f"Failed to send webhook for payment, id={payment_dto.id}, url={payment_dto.webhook_url}, error={str(e)}"
            )
            return False
