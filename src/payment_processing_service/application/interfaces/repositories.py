from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from payment_processing_service.domain.entities.payment import PaymentEntity


class PaymentRepositoryProtocol(Protocol):
    """Протокол для репозитория платежей."""

    @abstractmethod
    async def get_by_id(self, entity_id: str | UUID) -> PaymentEntity | None:
        """Получает платеж по ID."""

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str | UUID) -> PaymentEntity | None:
        """Получает платеж по idempotency_key."""

    @abstractmethod
    async def save(self, entity: PaymentEntity) -> None:
        """Сохраняет новый платеж или обновляет существующий."""
