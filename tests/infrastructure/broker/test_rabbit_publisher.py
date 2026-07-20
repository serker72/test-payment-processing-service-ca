"""Тесты для RabbitPublisher."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.broker.rabbit import RabbitPublisher
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper


@pytest.mark.unit
def _create_settings() -> Settings:
    """Создаёт Settings для тестов."""
    return Settings(
        consumer={
            "consumer_queue_name": "test.queue",
            "consumer_exchange_name": "test.exchange",
            "consumer_dlx_exchange_name": "test.dlx",
            "consumer_payment_routing_key": "test.routing",
            "consumer_queue_delivery_limit": 3,
            "consumer_dlq_queue_name": "test.dlq",
            "consumer_dlq_queue_message_ttl": 86400000,
            "consumer_dead_letter_routing_key": "test.dlq.routing",
        },
        broker={
            "broker_url": "amqp://test:test@localhost:5672/",
        },
    )


def _create_notification_dto() -> PaymentCreateNotificationDTO:
    """Создаёт PaymentCreateNotificationDTO для тестов."""
    return PaymentCreateNotificationDTO(
        payment_id=uuid4(),
        status=PaymentStatusDTO(value="pending"),
        created_at=datetime.now(UTC),
    )


class TestRabbitPublisher:
    """Тесты для RabbitPublisher."""

    @pytest.fixture
    def settings(self):
        return _create_settings()

    @pytest.fixture
    def broker_mock(self):
        mock = AsyncMock()
        mock.publish = AsyncMock()
        return mock

    @pytest.fixture
    def mapper(self):
        return InfrastructurePaymentMapper()

    @pytest.fixture
    def publisher(self, settings, broker_mock, mapper):
        return RabbitPublisher(
            settings=settings,
            broker=broker_mock,
            mapper=mapper,
        )

    async def test_publishes_notification(self, publisher, broker_mock):
        """Должен опубликовать notification в брокер."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        broker_mock.publish.assert_called_once()
        call_kwargs = broker_mock.publish.call_args[1]
        assert "message" in call_kwargs
        assert "queue" in call_kwargs
        assert "message_id" in call_kwargs

    async def test_publishes_to_correct_queue(self, publisher, broker_mock):
        """Должен опубликовать в правильную очередь."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        assert call_kwargs["queue"] == "test.queue"

    async def test_message_id_is_payment_id(self, publisher, broker_mock):
        """message_id должен быть payment_id."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        assert call_kwargs["message_id"] == str(dto.payment_id)

    async def test_message_contains_notification_data(self, publisher, broker_mock):
        """Сообщение должно содержать данные notification."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        message = call_kwargs["message"]
        assert "payment_id" in message
        assert "status" in message
        assert "created_at" in message

    async def test_raises_on_broker_error(self, publisher, broker_mock):
        """Должен выбросить исключение при ошибке брокера."""
        dto = _create_notification_dto()
        broker_mock.publish.side_effect = Exception("Connection refused")

        with pytest.raises(Exception, match="Connection refused"):
            await publisher.publish_new_payment(dto)
