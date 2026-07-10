from dataclasses import dataclass
from typing import final

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing_service.application.interfaces.repositories import PaymentRepositoryProtocol
from payment_processing_service.application.interfaces.uow import PaymentUnitOfWorkProtocol


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentSQLAlchemyUnitOfWork(PaymentUnitOfWorkProtocol):
    """Реализация шаблона Unit of Work в SQLAlchemy."""

    session: AsyncSession
    repository: PaymentRepositoryProtocol

    async def __aenter__(self) -> "PaymentSQLAlchemyUnitOfWork":
        """Выполняется при входе в асинхронный менеджер контекста."""
        logger.debug("Starting db transaction")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Выполняется при выходе из асинхронного менеджера контекста."""
        if exc_type is not None:
            logger.warning("Transaction rolled back due to exception: %s - %s", exc_type.__name__, str(exc_val))
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Подтверждает текущую транзакцию."""
        logger.debug("Committing transaction")
        await self.session.commit()
        logger.debug("Transaction committed successfully")

    async def rollback(self) -> None:
        """Откатывает текущую транзакцию."""
        logger.debug("Rolling back transaction")
        await self.session.rollback()
        logger.debug("Transaction rolled back successfully")
