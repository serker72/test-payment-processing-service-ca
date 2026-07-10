from abc import abstractmethod
from typing import Protocol

from payment_processing_service.application.dtos.payment import PaymentCreateNotificationDTO, PaymentDTO


class PaymentSerializationMapperProtocol(Protocol):
    """Протокол сериализации/десериализации DTO приложений."""

    @abstractmethod
    def to_dict(self, dto: PaymentDTO) -> dict:
        """Преобразует PaymentDTO в словарь для сериализации JSON."""

    @abstractmethod
    def from_dict(self, data: dict) -> PaymentDTO:
        """Преобразует словарь из десериализации JSON в PaymentDTO."""

    @abstractmethod
    def to_notification_dict(self, dto: PaymentCreateNotificationDTO) -> dict:
        """Преобразует PaymentCreateNotificationDTO в словарь для коммуникации с помощью брокера сообщений."""
