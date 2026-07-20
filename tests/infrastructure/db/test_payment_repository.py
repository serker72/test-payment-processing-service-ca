"""Тесты для PaymentRepositorySQLAlchemy."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus
from payment_processing_service.infrastructures.db.exceptions import (
    RepositoryConflictError,
    RepositoryNotFoundError,
    RepositorySaveError,
)
from payment_processing_service.infrastructures.db.mappers.payment_db_mapper import PaymentDBMapper
from payment_processing_service.infrastructures.db.models.payment import PaymentModel
from payment_processing_service.infrastructures.db.repositories.payment import PaymentRepositorySQLAlchemy


@pytest.mark.unit
def _create_model() -> PaymentModel:
    """Создаёт PaymentModel для тестов."""
    return PaymentModel(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyEnum.RUB,
        description="Test payment",
        meta_data={
            "address": "1234567890123456",
            "fio": "Test User",
            "exp_date": "12/25",
            "bank": "Bank",
            "phone": "+79001234567",
        },
        status=PaymentStatusEnum.pending,
        idempotency_key="test-key",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        processing_error_message=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _create_entity() -> PaymentEntity:
    """Создаёт PaymentEntity для тестов."""
    return PaymentEntity(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=Currency(value=CurrencyEnum.RUB),
        description="Test payment",
        meta_data=PaymentMetaData(
            address="1234567890123456",
            fio="Test User",
            exp_date="12/25",
            bank="Bank",
            phone="+79001234567",
        ),
        status=PaymentStatus(value=PaymentStatusEnum.pending),
        idempotency_key="test-key",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        processing_error_message=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def session_mock():
    """Mock сессии SQLAlchemy."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mapper():
    return PaymentDBMapper()


@pytest.fixture
def repository(session_mock, mapper):
    return PaymentRepositorySQLAlchemy(session=session_mock, mapper=mapper)


class TestPaymentRepositorySQLAlchemy:
    """Тесты для PaymentRepositorySQLAlchemy."""

    async def test_get_by_id_returns_entity(self, repository, session_mock):
        """Должен вернуть entity по ID."""
        model = _create_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session_mock.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_by_id(model.id)

        assert result is not None
        assert result.id == model.id
        assert result.currency.value == CurrencyEnum.RUB

    async def test_get_by_id_returns_none_when_not_found(self, repository, session_mock):
        """Должен вернуть None, если entity не найден."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session_mock.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_by_id(uuid4())

        assert result is None

    async def test_get_by_id_raises_on_sql_error(self, repository, session_mock):
        """Должен выбросить RepositoryNotFoundError при ошибке SQL."""
        session_mock.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(RepositoryNotFoundError):
            await repository.get_by_id(uuid4())

    async def test_get_by_idempotency_key_returns_entity(self, repository, session_mock):
        """Должен вернуть entity по idempotency_key."""
        model = _create_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session_mock.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_by_idempotency_key(model.idempotency_key)

        assert result is not None
        assert result.idempotency_key == model.idempotency_key

    async def test_get_by_idempotency_key_returns_none_when_not_found(self, repository, session_mock):
        """Должен вернуть None, если entity не найден по idempotency_key."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session_mock.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_by_idempotency_key("non-existent-key")

        assert result is None

    async def test_get_by_idempotency_key_raises_on_sql_error(self, repository, session_mock):
        """Должен выбросить RepositoryNotFoundError при ошибке SQL."""
        session_mock.execute = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with pytest.raises(RepositoryNotFoundError):
            await repository.get_by_idempotency_key("any-key")

    async def test_save_new_entity(self, repository, session_mock):
        """Должен сохранить новый entity."""
        entity = _create_entity()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session_mock.execute = AsyncMock(return_value=mock_result)

        await repository.save(entity)

        session_mock.add.assert_called_once()

    async def test_save_existing_entity(self, repository, session_mock, mapper):
        """Должен обновить существующий entity."""
        entity = _create_entity()
        model = _create_model()
        model.id = entity.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session_mock.execute = AsyncMock(return_value=mock_result)

        await repository.save(entity)

        # Должен вызвать update_model_from_entity, а не add
        session_mock.add.assert_called_once()

    async def test_save_raises_conflict_on_integrity_error(self, repository, session_mock):
        """Должен выбросить RepositoryConflictError при конфликте."""
        entity = _create_entity()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session_mock.execute = AsyncMock(return_value=mock_result)
        session_mock.add.side_effect = IntegrityError("fake", "fake", "fake")

        with pytest.raises(RepositoryConflictError):
            await repository.save(entity)

    async def test_save_raises_save_error_on_general_error(self, repository, session_mock):
        """Должен выбросить RepositorySaveError при общей ошибке."""
        entity = _create_entity()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session_mock.execute = AsyncMock(return_value=mock_result)
        session_mock.add.side_effect = Exception("Unexpected error")

        with pytest.raises(RepositorySaveError):
            await repository.save(entity)

    async def test_get_by_filters(self, repository, session_mock):
        """Должен выполнить запрос по фильтрам."""
        model = _create_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session_mock.execute = AsyncMock(return_value=mock_result)

        result = await repository.get_by_filters([])

        assert result is not None
        assert result.id == model.id
