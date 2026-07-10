from typing import final

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from payment_processing_service.application.interfaces.db_mapper import DbMapperProtocol
from payment_processing_service.infrastructures.db.models.payment import PaymentModel


@final
class PaymentUoWMapper(DbMapperProtocol[PaymentModel]):
    """Mapper для PaymentModel для работы с паттерном Unit of Work."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def insert(self, model: PaymentModel) -> None:
        """Вставляет новую PaymentModel в базу данных."""
        self.session.add(model)
        logger.debug(f"Added PaymentModel {model.id} to session")

    def update(self, model: PaymentModel) -> None:
        """Обновляет существующую PaymentModel в базе данных."""
        self.session.merge(model)
        logger.debug(f"Merged PaymentModel {model.id} into session")

    def delete(self, model: PaymentModel) -> None:
        """Удаляет PaymentModel из базы данных."""
        self.session.delete(model)
        logger.debug(f"Deleted PaymentModel {model.id} from session")
