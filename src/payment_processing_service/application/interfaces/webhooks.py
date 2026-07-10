from abc import abstractmethod
from typing import Protocol

from payment_processing_service.application.dtos.payment import PaymentDTO


class SendPaymentWebhookProtocol(Protocol):
    """Протокол публикации сообщений о платежах в брокере сообщений."""

    @abstractmethod
    async def send_webhook(self, dto: PaymentDTO) -> None:
        """Отправка вебхука для платежа."""
