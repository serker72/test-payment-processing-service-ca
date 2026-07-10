from dataclasses import dataclass
from typing import final

import httpx
import stamina
from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.interfaces.webhooks import SendPaymentWebhookProtocol
from payment_processing_service.domain.exceptions import WebhookDeliveryError
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SendPaymentWebhookClient(SendPaymentWebhookProtocol):
    """Клиент для отправки вебхука для платежа."""

    client: httpx.AsyncClient
    mapper: InfrastructurePaymentMapper

    @stamina.retry(
        on=(httpx.HTTPError, httpx.RequestError),
        attempts=3,
        wait_initial=1.0,
        wait_jitter=1.0,
    )
    async def send_webhook(self, dto: PaymentDTO) -> None:
        """Отправка вебхука для платежа."""
        payload = self.mapper.to_dict(dto)

        try:
            response = await self.client.post(dto.webhook_url, json=payload, timeout=httpx.Timeout(10.0))
            response.raise_for_status()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.exception(f"Error during HTTP request, url={dto.webhook_url}, error={str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Webhook for payment send unexpected error, error={str(e)}")
            raise WebhookDeliveryError("Failed to send webhook for payment: %s", e) from e
