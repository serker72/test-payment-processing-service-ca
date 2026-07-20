"""Тесты для SendPaymentWebhookClient."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.domain.exceptions import WebhookDeliveryError
from payment_processing_service.infrastructures.http.clients import SendPaymentWebhookClient
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper


@pytest.mark.unit
def _create_dto() -> PaymentDTO:
    """Создаёт PaymentDTO для тестов."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(
            address="1234567890123456",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        ),
        status=PaymentStatusDTO(value="pending"),
        idempotency_key="test-key",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestSendPaymentWebhookClient:
    """Тесты для SendPaymentWebhookClient."""

    @pytest.fixture
    def http_client_mock(self):
        mock = AsyncMock(spec=httpx.AsyncClient)
        mock.post = AsyncMock()
        return mock

    @pytest.fixture
    def mapper(self):
        return InfrastructurePaymentMapper()

    @pytest.fixture
    def client(self, http_client_mock, mapper):
        return SendPaymentWebhookClient(
            client=http_client_mock,
            mapper=mapper,
        )

    async def test_sends_webhook_successfully(self, client, http_client_mock):
        """Должен успешно отправить вебхук."""
        dto = _create_dto()
        response_mock = MagicMock()
        response_mock.raise_for_status = MagicMock()
        http_client_mock.post = AsyncMock(return_value=response_mock)

        await client.send_webhook(dto)

        http_client_mock.post.assert_called_once()
        call_args = http_client_mock.post.call_args
        assert call_args[0][0] == dto.webhook_url
        assert "id" in call_args[1]["json"]

    async def test_post_called_with_correct_url(self, client, http_client_mock):
        """Должен вызвать POST с правильным URL."""
        dto = _create_dto()
        response_mock = MagicMock()
        response_mock.raise_for_status = MagicMock()
        http_client_mock.post = AsyncMock(return_value=response_mock)

        await client.send_webhook(dto)

        call_args = http_client_mock.post.call_args
        assert call_args[0][0] == "https://example.com/webhook"

    async def test_post_called_with_json_payload(self, client, http_client_mock):
        """Должен передать JSON payload в POST."""
        dto = _create_dto()
        response_mock = MagicMock()
        response_mock.raise_for_status = MagicMock()
        http_client_mock.post = AsyncMock(return_value=response_mock)

        await client.send_webhook(dto)

        call_args = http_client_mock.post.call_args
        assert "json" in call_args[1]
        assert "id" in call_args[1]["json"]
        assert "amount" in call_args[1]["json"]

    async def test_raises_http_status_error(self, client, http_client_mock):
        """Должен выбросить HTTPStatusError при ошибке HTTP."""
        dto = _create_dto()
        response_mock = MagicMock()
        response_mock.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=MagicMock()
        )
        http_client_mock.post = AsyncMock(return_value=response_mock)

        with pytest.raises(httpx.HTTPStatusError):
            await client.send_webhook(dto)

    async def test_raises_request_error(self, client, http_client_mock):
        """Должен выбросить RequestError при ошибке запроса."""
        dto = _create_dto()
        http_client_mock.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

        with pytest.raises(httpx.RequestError):
            await client.send_webhook(dto)

    async def test_timeout_is_set(self, client, http_client_mock):
        """Должен установить тайм-аут для запроса."""
        dto = _create_dto()
        response_mock = MagicMock()
        response_mock.raise_for_status = MagicMock()
        http_client_mock.post = AsyncMock(return_value=response_mock)

        await client.send_webhook(dto)

        call_args = http_client_mock.post.call_args
        assert call_args[1]["timeout"] == httpx.Timeout(10.0)
