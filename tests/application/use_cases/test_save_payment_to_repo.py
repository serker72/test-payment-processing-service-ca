"""Тесты для use case SavePaymentToRepo."""

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
from payment_processing_service.application.use_cases.save_payment_to_repo import SavePaymentToRepoUseCase


@pytest.mark.unit
def _create_dto(**kwargs) -> PaymentDTO:
    """Фабрика PaymentDTO."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
        status=PaymentStatusDTO(value="pending"),
        idempotency_key="test-key",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        **kwargs,
    )


class TestSavePaymentToRepoUseCase:
    """Тесты для SavePaymentToRepoUseCase."""

    @pytest.fixture
    def mock_uow(self):
        mock = MagicMock()
        mock.repository = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=None)
        mock.commit = AsyncMock()
        mock.rollback = AsyncMock()
        return mock

    @pytest.fixture
    def mock_mapper(self):
        mock = MagicMock()
        return mock

    @pytest.fixture
    def use_case(self, mock_uow, mock_mapper):
        return SavePaymentToRepoUseCase(uow=mock_uow, payment_mapper=mock_mapper)

    async def test_saves_entity_to_repository(self, use_case, mock_uow, mock_mapper):
        """Должен сохранить entity в репозиторий."""
        dto = _create_dto()
        entity = MagicMock()
        mock_mapper.to_entity.return_value = entity

        await use_case(dto)

        mock_mapper.to_entity.assert_called_once_with(dto)
        mock_uow.repository.save.assert_called_once_with(entity)

    async def test_uses_uow_context_manager(self, use_case, mock_uow, mock_mapper):
        """Должен использовать UoW как контекстный менеджер."""
        dto = _create_dto()
        mock_mapper.to_entity.return_value = MagicMock()

        await use_case(dto)

        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()

    async def test_mapper_converts_dto_to_entity(self, use_case, mock_uow, mock_mapper):
        """Маппер должен преобразовать DTO в entity."""
        dto = _create_dto()

        await use_case(dto)

        mock_mapper.to_entity.assert_called_once_with(dto)
