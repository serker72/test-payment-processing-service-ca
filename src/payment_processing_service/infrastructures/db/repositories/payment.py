from dataclasses import dataclass
from typing import final
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import BinaryExpression, ColumnElement

from payment_processing_service.application.interfaces.repositories import PaymentRepositoryProtocol
from payment_processing_service.domain.entities.payment import PaymentEntity
from payment_processing_service.infrastructures.db.exceptions import (
    RepositoryConflictError,
    RepositoryNotFoundError,
    RepositorySaveError,
)
from payment_processing_service.infrastructures.db.mappers import PaymentDBMapper
from payment_processing_service.infrastructures.db.models.payment import PaymentModel


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentRepositorySQLAlchemy(PaymentRepositoryProtocol):
    """SQLAlchemy реализация протокола PaymentRepositoryProtocol."""

    session: AsyncSession
    mapper: PaymentDBMapper

    async def get_by_filters(self, filters: list[BinaryExpression | ColumnElement]) -> PaymentEntity | None:
        """Получает платеж по списку фильтров."""
        statement = select(PaymentModel).where(*filters)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, entity_id: str | UUID) -> PaymentEntity | None:
        """Получает платеж по ID."""
        try:
            entity_model = await self.get_by_filters([PaymentModel.id == entity_id])
            return self.mapper.to_entity(entity_model) if entity_model else None
        except SQLAlchemyError as e:
            raise RepositoryNotFoundError(f"Failed to retrieve payment by id '{entity_id}': {e}") from e

    async def get_by_idempotency_key(self, idempotency_key: str | UUID) -> PaymentEntity | None:
        """Получает платеж по idempotency_key."""
        try:
            entity_model = await self.get_by_filters([PaymentModel.idempotency_key == idempotency_key])
            return self.mapper.to_entity(entity_model) if entity_model else None
        except SQLAlchemyError as e:
            raise RepositoryNotFoundError(
                f"Failed to retrieve payment by idempotency_key '{idempotency_key}': {e}"
            ) from e

    async def save(self, entity: PaymentEntity) -> None:
        """Сохраняет новый платеж или обновляет существующий."""
        try:
            entity_model = await self.get_by_filters([PaymentModel.id == entity.id])

            if entity_model:
                # Обновить существующую модель с помощью mapper
                self.mapper.update_model_from_entity(entity_model, entity)
            else:
                # Создать новую модель с помощью mapper
                entity_model = self.mapper.to_model(entity)

            self.session.add(entity_model)
        except IntegrityError as e:
            raise RepositoryConflictError(f"Conflict while saving payment '{entity.id}': {e}") from e
        except SQLAlchemyError as e:
            raise RepositorySaveError(f"Failed to save payment '{entity.id}': {e}") from e
        except Exception as e:
            raise RepositorySaveError(f"Unexpected error while saving payment '{entity.id}': {e}") from e
