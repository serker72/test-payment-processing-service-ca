from abc import abstractmethod
from typing import Protocol

from payment_processing_service.application.dtos.payment import PaymentCreateNotificationDTO


class PaymentMessageBrokerPublisherProtocol(Protocol):
    """Протокол публикации сообщений о платежах в брокере сообщений."""

    @abstractmethod
    async def publish_new_payment(self, notification_dto: PaymentCreateNotificationDTO) -> None:
        """Публикует уведомление о приёме платежа в брокере сообщений."""
