"""Тесты для use case CreatePayment."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.use_cases.create_payment import CreatePaymentUseCase
from payment_processing_service.config.enums import PaymentStatusEnum


@pytest.mark.unit
def _create_dto(**kwargs) -> PaymentDTO:
    """Фабрика PaymentDTO."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
        status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
        idempotency_key="unique-key-1",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        **kwargs,
    )


class TestCreatePaymentUseCase:
    """Тесты для CreatePaymentUseCase."""

    async def test_creates_new_payment(self):
        """Должен создавать новый платёж, если его нет по idempotency_key."""
        mock_get_by_id = AsyncMock(return_value=None)
        mock_get_by_idempotency_key = AsyncMock(return_value=None)
        mock_save = AsyncMock()
        mock_publish = AsyncMock()

        dto = _create_dto()
        mock_get_by_id.return_value = dto

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        result = await use_case(dto)

        mock_save.assert_called_once_with(dto)
        mock_publish.assert_called_once_with(dto)
        mock_get_by_id.assert_called_once_with(str(dto.id))
        assert result.id == dto.id

    async def test_returns_existing_payment_on_duplicate_key(self):
        """Должен возвращать существующий платёж, если idempotency_key уже занят."""
        mock_get_by_id = AsyncMock()
        mock_get_by_idempotency_key = AsyncMock()
        mock_save = AsyncMock()
        mock_publish = AsyncMock()

        existing_id = uuid4()
        existing_dto = PaymentDTO(
            id=existing_id,
            amount=Decimal("1500.00"),
            currency=CurrencyDTO(value="RUB"),
            description="Test payment",
            meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
            status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
            idempotency_key="existing-key",
            webhook_url="https://example.com/webhook",
            expired_at=datetime.now(timezone.utc),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_get_by_idempotency_key.return_value = existing_dto

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        new_dto = PaymentDTO(
            id=uuid4(),
            amount=Decimal("1500.00"),
            currency=CurrencyDTO(value="RUB"),
            description="Test payment",
            meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
            status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
            idempotency_key="existing-key",
            webhook_url="https://example.com/webhook",
            expired_at=datetime.now(timezone.utc),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        result = await use_case(new_dto)

        mock_save.assert_not_called()
        mock_publish.assert_not_called()
        assert result.id == existing_id
        assert result.idempotency_key == existing_dto.idempotency_key

    async def test_continues_on_publish_failure(self):
        """При ошибке публикации платёж всё равно должен быть создан."""
        mock_get_by_id = AsyncMock()
        mock_get_by_idempotency_key = AsyncMock(return_value=None)
        mock_save = AsyncMock()
        mock_publish = AsyncMock(side_effect=Exception("Broker unavailable"))

        dto = _create_dto()
        mock_get_by_id.return_value = dto

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        result = await use_case(dto)

        mock_save.assert_called_once_with(dto)
        assert result.id == dto.id

    async def test_save_called_with_correct_dto(self):
        """Save должен вызываться с правильным DTO."""
        mock_get_by_id = AsyncMock()
        mock_get_by_idempotency_key = AsyncMock(return_value=None)
        mock_save = AsyncMock()
        mock_publish = AsyncMock()

        dto = _create_dto()
        mock_get_by_id.return_value = dto

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        await use_case(dto)

        mock_save.assert_called_once_with(dto)

    async def test_get_by_id_called_after_save(self):
        """После сохранения должен вызываться get_by_id для получения результата."""
        mock_get_by_id = AsyncMock()
        mock_get_by_idempotency_key = AsyncMock(return_value=None)
        mock_save = AsyncMock()
        mock_publish = AsyncMock()

        dto = _create_dto()
        mock_get_by_id.return_value = dto

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        await use_case(dto)

        mock_get_by_id.assert_called_once_with(str(dto.id))

    async def test_returns_none_when_get_by_id_returns_none(self):
        """Если get_by_id возвращает None, должен возвращаться None."""
        mock_get_by_id = AsyncMock(return_value=None)
        mock_get_by_idempotency_key = AsyncMock(return_value=None)
        mock_save = AsyncMock()
        mock_publish = AsyncMock()

        dto = _create_dto()

        use_case = CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=mock_get_by_id,
            get_payment_by_idempotency_key_from_repo_use_case=mock_get_by_idempotency_key,
            save_payment_to_repo_use_case=mock_save,
            publish_payment_to_broker_use_case=mock_publish,
        )

        result = await use_case(dto)

        mock_save.assert_called_once_with(dto)
        assert result is None
