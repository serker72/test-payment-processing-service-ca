"""Тесты для use case GetPaymentByIdFromRepoUseCase."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.use_cases.get_payment_from_repo import (
    GetPaymentByIdempotencyKeyFromRepoUseCase,
    GetPaymentByIdFromRepoUseCase,
)
from payment_processing_service.domain.entities.payment import PaymentEntity
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


@pytest.mark.unit
def _create_entity() -> PaymentEntity:
    """Фабрика PaymentEntity."""
    return PaymentEntity(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=Currency(value="RUB"),
        description="Test payment",
        meta_data=PaymentEntity.__dataclass_fields__["meta_data"].default_factory()
        if hasattr(PaymentEntity, "__dataclass_fields__")
        else MagicMock(),
        status=PaymentStatus(value="pending"),
        idempotency_key="test-key",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mapper_mock():
    mock = MagicMock()
    return mock


class TestGetPaymentByIdFromRepoUseCase:
    """Тесты для GetPaymentByIdFromRepoUseCase."""

    @pytest.fixture
    def mock_uow(self):
        mock = MagicMock()
        mock.repository = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def use_case(self, mock_uow, mapper_mock):
        return GetPaymentByIdFromRepoUseCase(uow=mock_uow, payment_mapper=mapper_mock)

    async def test_returns_dto_when_entity_found(self, use_case, mapper_mock):
        """Должен вернуть DTO, если entity найден."""
        entity = MagicMock()
        expected_dto = MagicMock()
        mapper_mock.to_dto.return_value = expected_dto
        use_case.uow.repository.get_by_id = AsyncMock(return_value=entity)

        result = await use_case("test-entity-id")

        use_case.uow.repository.get_by_id.assert_called_once_with("test-entity-id")
        mapper_mock.to_dto.assert_called_once_with(entity)
        assert result == expected_dto

    async def test_returns_none_when_entity_not_found(self, use_case, mapper_mock):
        """Должен вернуть None, если entity не найден."""
        use_case.uow.repository.get_by_id = AsyncMock(return_value=None)

        result = await use_case("non-existent-id")

        use_case.uow.repository.get_by_id.assert_called_once_with("non-existent-id")
        mapper_mock.to_dto.assert_not_called()
        assert result is None

    async def test_uses_uow_context_manager(self, use_case, mapper_mock):
        """Должен использовать UoW как контекстный менеджер."""
        mapper_mock.to_dto.return_value = MagicMock()
        use_case.uow.repository.get_by_id = AsyncMock(return_value=MagicMock())

        await use_case("test-id")

        use_case.uow.__aenter__.assert_called_once()
        use_case.uow.__aexit__.assert_called_once()


class TestGetPaymentByIdempotencyKeyFromRepoUseCase:
    """Тесты для GetPaymentByIdempotencyKeyFromRepoUseCase."""

    @pytest.fixture
    def mock_uow(self):
        mock = MagicMock()
        mock.repository = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def use_case(self, mock_uow, mapper_mock):
        return GetPaymentByIdempotencyKeyFromRepoUseCase(uow=mock_uow, payment_mapper=mapper_mock)

    async def test_returns_dto_when_entity_found(self, use_case, mapper_mock):
        """Должен вернуть DTO, если entity найден по idempotency_key."""
        entity = MagicMock()
        expected_dto = MagicMock()
        mapper_mock.to_dto.return_value = expected_dto
        use_case.uow.repository.get_by_idempotency_key = AsyncMock(return_value=entity)

        result = await use_case("my-idempotency-key")

        use_case.uow.repository.get_by_idempotency_key.assert_called_once_with("my-idempotency-key")
        mapper_mock.to_dto.assert_called_once_with(entity)
        assert result == expected_dto

    async def test_returns_none_when_entity_not_found(self, use_case, mapper_mock):
        """Должен вернуть None, если entity не найден."""
        use_case.uow.repository.get_by_idempotency_key = AsyncMock(return_value=None)

        result = await use_case("non-existent-key")

        use_case.uow.repository.get_by_idempotency_key.assert_called_once_with("non-existent-key")
        mapper_mock.to_dto.assert_not_called()
        assert result is None

    async def test_uses_uow_context_manager(self, use_case, mapper_mock):
        """Должен использовать UoW как контекстный менеджер."""
        mapper_mock.to_dto.return_value = MagicMock()
        use_case.uow.repository.get_by_idempotency_key = AsyncMock(return_value=MagicMock())

        await use_case("test-key")

        use_case.uow.__aenter__.assert_called_once()
        use_case.uow.__aexit__.assert_called_once()
