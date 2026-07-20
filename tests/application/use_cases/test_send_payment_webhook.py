"""Тесты для use case SendPaymentWebhook."""

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
from payment_processing_service.application.use_cases.send_payment_webhook import SendPaymentWebhookUseCase
from payment_processing_service.domain.exceptions import WebhookDeliveryError


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
        webhook_url="https://example.com/webhook",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        **kwargs,
    )


class TestSendPaymentWebhookUseCase:
    """Тесты для SendPaymentWebhookUseCase."""

    @pytest.fixture
    def mock_http_client(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_mapper(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_http_client, mock_mapper):
        return SendPaymentWebhookUseCase(
            http_client=mock_http_client,
            payment_mapper=mock_mapper,
        )

    async def test_sends_webhook(self, use_case, mock_http_client):
        """Должен отправить вебхук."""
        dto = _create_dto()

        await use_case(dto)

        mock_http_client.send_webhook.assert_called_once_with(dto)

    async def test_handles_webhook_error(self, use_case, mock_http_client):
        """Должен обработать ошибку отправки вебхука."""
        dto = _create_dto()
        mock_http_client.send_webhook.side_effect = WebhookDeliveryError("Failed")

        # Не должен выбрасывать исключение — use case его перехватывает
        await use_case(dto)

        mock_http_client.send_webhook.assert_called_once_with(dto)

    async def test_does_not_reraise_webhook_error(self, use_case, mock_http_client):
        """Исключение WebhookDeliveryError не должно быть переброшено."""
        dto = _create_dto()
        mock_http_client.send_webhook.side_effect = WebhookDeliveryError("Delivery failed")

        # Должен завершиться без исключения
        await use_case(dto)
        mock_http_client.send_webhook.assert_called_once_with(dto)
