"""Тесты для use case ExecutePayment."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.use_cases.execute_payment import ExecutePaymentUseCase
from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.config.settings import Settings


@pytest.fixture
def settings():
    """Настройки для use case."""
    return Settings()


@pytest.fixture
def sample_dto():
    """Создаёт PaymentDTO для тестов."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
        status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
        idempotency_key="test-key",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.mark.unit
class TestExecutePaymentUseCase:
    """Тесты для ExecutePaymentUseCase."""

    async def test_success_status_when_rate_high(self, settings, sample_dto):
        """При высокой ставке успеха платёж должен завершиться succeeded."""
        settings.app.backend_payment_success_rate = 1.0
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await use_case(sample_dto)

        assert result.status.value == PaymentStatusEnum.succeeded
        assert result.processing_error_message is None
        assert result.id == sample_dto.id

    async def test_failed_status_when_rate_low(self, settings, sample_dto):
        """При низкой ставке успеха платёж должен завершиться failed."""
        settings.app.backend_payment_success_rate = 0.0
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await use_case(sample_dto)

        assert result.status.value == PaymentStatusEnum.failed
        assert result.processing_error_message is not None
        assert result.id == sample_dto.id

    async def test_expired_payment_fails(self, settings, sample_dto):
        """Просроченный платёж должен завершиться failed."""
        settings.app.backend_payment_success_rate = 1.0
        from dataclasses import replace

        sample_dto_expired = replace(sample_dto, expired_at=datetime.now(timezone.utc))
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await use_case(sample_dto_expired)

        assert result.status.value == PaymentStatusEnum.failed
        assert result.processing_error_message is not None

    async def test_updated_at_is_changed(self, settings, sample_dto):
        """updated_at должен обновляться после выполнения."""
        settings.app.backend_payment_success_rate = 1.0
        original_updated_at = sample_dto.updated_at
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await use_case(sample_dto)

        assert result.updated_at > original_updated_at

    async def test_original_dto_not_modified(self, settings, sample_dto):
        """Исходный DTO не должен модифицироваться (frozen dataclass)."""
        settings.app.backend_payment_success_rate = 1.0
        original_status = sample_dto.status
        original_error = sample_dto.processing_error_message
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await use_case(sample_dto)

        assert sample_dto.status == original_status
        assert sample_dto.processing_error_message == original_error

    async def test_error_message_in_failed_status(self, settings, sample_dto):
        """При failed статусе должно быть сообщение об ошибке."""
        settings.app.backend_payment_success_rate = 0.0
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await use_case(sample_dto)

        error_messages = [
            "Insufficient funds",
            "Incorrect card/wallet number",
            "Payment declined by the bank",
            "Suspected fraud",
            "Processing time expired",
        ]
        assert result.processing_error_message in error_messages

    async def test_zero_delay_when_min_max_zero(self, settings, sample_dto):
        """При min_delay=0 и max_delay=0 задержка должна быть нулевой."""
        settings.app.backend_payment_success_rate = 1.0
        settings.app.backend_payment_min_delay = 0
        settings.app.backend_payment_max_delay = 0
        use_case = ExecutePaymentUseCase(settings=settings)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await use_case(sample_dto)

        assert result.status.value == PaymentStatusEnum.succeeded
        mock_sleep.assert_called_once()
