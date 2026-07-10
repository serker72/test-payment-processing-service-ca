from abc import abstractmethod
from typing import Protocol

from payment_processing_service.application.dtos.payment import PaymentCreateNotificationDTO, PaymentDTO
from payment_processing_service.domain.entities.payment import PaymentEntity


class DtoPaymentEntityMapperProtocol(Protocol):
    """Протокол отображения данных платежа для слоя Application (Domain Entity <-> Application DTO)."""

    @abstractmethod
    def to_dto(self, entity: PaymentEntity) -> PaymentDTO:
        """Преобразует доменную сущность в объект передачи данных."""

    @abstractmethod
    def to_entity(self, dto: PaymentDTO) -> PaymentEntity:
        """Преобразует объект передачи данных в доменную сущность."""

    @abstractmethod
    def to_notification_dto(self, dto: PaymentDTO) -> PaymentCreateNotificationDTO:
        """Преобразует доменную сущность в объект передачи данных для уведомлений."""
