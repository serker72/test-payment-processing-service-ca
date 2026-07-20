"""Тесты для use case ProcessPayment."""

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
from payment_processing_service.application.use_cases.process_payment import ProcessPaymentUseCase
from payment_processing_service.config.enums import PaymentStatusEnum


@pytest.mark.unit
def _create_dto(status: str = PaymentStatusEnum.pending, webhook_url: str | None = None, **kwargs) -> PaymentDTO:
    """Фабрика PaymentDTO."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Ivan Ivanov"),
        status=PaymentStatusDTO(value=status),
        idempotency_key="test-key",
        webhook_url=webhook_url,
        expired_at=datetime.now(timezone.utc),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        **kwargs,
    )


class TestProcessPaymentUseCase:
    """Тесты для ProcessPaymentUseCase."""

    @pytest.fixture
    def mock_get_payment(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_execute(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_save(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_send_webhook(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_uow(self):
        mock_uow = MagicMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        mock_uow.commit = AsyncMock()
        mock_uow.rollback = AsyncMock()
        mock_uow.repository = AsyncMock()
        return mock_uow

    @pytest.fixture
    def use_case(self, mock_uow, mock_get_payment, mock_execute, mock_save, mock_send_webhook):
        return ProcessPaymentUseCase(
            uow=mock_uow,
            get_payment_by_id_from_repo_use_case=mock_get_payment,
            execute_payment_use_case=mock_execute,
            save_payment_to_repo_use_case=mock_save,
            send_payment_webhook_use_case=mock_send_webhook,
        )

    async def test_processes_pending_payment(
        self, use_case, mock_get_payment, mock_execute, mock_save, mock_send_webhook
    ):
        """Должен обработать pending платёж."""
        dto = _create_dto(status=PaymentStatusEnum.pending)
        updated_dto = _create_dto(status=PaymentStatusEnum.succeeded)
        mock_get_payment.return_value = dto
        mock_execute.return_value = updated_dto

        await use_case({"payment_id": str(dto.id)})

        mock_execute.assert_called_once_with(dto)
        mock_save.assert_called_once_with(updated_dto)

    async def test_skips_non_pending_payment(self, use_case, mock_get_payment, mock_execute, mock_save):
        """Должен пропустить платёж со статусом не pending."""
        dto = _create_dto(status=PaymentStatusEnum.succeeded)
        mock_get_payment.return_value = dto

        await use_case({"payment_id": str(dto.id)})

        mock_execute.assert_not_called()
        mock_save.assert_not_called()

    async def test_skips_when_payment_not_found(self, use_case, mock_get_payment, mock_execute, mock_save):
        """Должен пропустить, если платёж не найден."""
        mock_get_payment.return_value = None

        await use_case({"payment_id": "non-existent-id"})

        mock_execute.assert_not_called()
        mock_save.assert_not_called()

    async def test_sends_webhook_when_url_present(
        self, use_case, mock_get_payment, mock_execute, mock_save, mock_send_webhook
    ):
        """Должен отправить вебхук, если webhook_url указан."""
        dto = _create_dto(status=PaymentStatusEnum.pending, webhook_url="https://example.com/hook")
        updated_dto = _create_dto(status=PaymentStatusEnum.succeeded, webhook_url="https://example.com/hook")
        mock_get_payment.return_value = dto
        mock_execute.return_value = updated_dto

        await use_case({"payment_id": str(dto.id)})

        mock_send_webhook.assert_called_once_with(updated_dto)

    async def test_skips_webhook_when_url_absent(
        self, use_case, mock_get_payment, mock_execute, mock_save, mock_send_webhook
    ):
        """Должен пропустить отправку вебхука, если webhook_url пустой."""
        dto = _create_dto(status=PaymentStatusEnum.pending, webhook_url=None)
        updated_dto = _create_dto(status=PaymentStatusEnum.succeeded, webhook_url=None)
        mock_get_payment.return_value = dto
        mock_execute.return_value = updated_dto

        await use_case({"payment_id": str(dto.id)})

        mock_send_webhook.assert_not_called()

    async def test_uses_uow_context_manager(self, use_case, mock_get_payment, mock_execute, mock_save):
        """Должен использовать UoW как контекстный менеджер."""
        dto = _create_dto(status=PaymentStatusEnum.pending)
        updated_dto = _create_dto(status=PaymentStatusEnum.succeeded)
        mock_get_payment.return_value = dto
        mock_execute.return_value = updated_dto

        mock_uow = use_case.uow
        await use_case({"payment_id": str(dto.id)})

        mock_uow.__aenter__.assert_called_once()
        mock_uow.__aexit__.assert_called_once()
