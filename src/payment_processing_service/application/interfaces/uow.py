from abc import abstractmethod
from typing import Protocol

from payment_processing_service.application.interfaces.repositories import PaymentRepositoryProtocol


class PaymentUnitOfWorkProtocol(Protocol):
    """Протокол для Unit of Work платежей."""

    repository: PaymentRepositoryProtocol

    @abstractmethod
    async def __aenter__(self) -> "PaymentUnitOfWorkProtocol":
        """Выполняется при входе в асинхронный менеджер контекста."""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Выполняется при выходе из асинхронного менеджера контекста."""

    @abstractmethod
    async def commit(self) -> None:
        """Подтверждает текущую транзакцию."""

    @abstractmethod
    async def rollback(self) -> None:
        """Откатывает текущую транзакцию."""
