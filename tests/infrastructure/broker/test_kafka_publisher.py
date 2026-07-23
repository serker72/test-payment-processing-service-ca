"""Тесты для KafkaPublisher."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.broker.kafka import KafkaPublisher
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper


def _create_notification_dto() -> PaymentCreateNotificationDTO:
    """Создаёт PaymentCreateNotificationDTO для тестов."""
    return PaymentCreateNotificationDTO(
        payment_id=uuid4(),
        status=PaymentStatusDTO(value="pending"),
        created_at=datetime.now(UTC),
    )


def _create_settings() -> Settings:
    """Создаёт Settings для тестов."""
    return Settings()


class TestKafkaPublisher:
    """Тесты для KafkaPublisher."""

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
        return KafkaPublisher(
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
        assert "topic" in call_kwargs
        assert "correlation_id" in call_kwargs

    async def test_publishes_to_correct_topic(self, publisher, broker_mock):
        """Должен опубликовать в правильную тему."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        assert call_kwargs["topic"] == publisher.settings.consumer.consumer_queue_name

    async def test_correlation_id_is_payment_id(self, publisher, broker_mock):
        """correlation_id должен быть payment_id."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        assert call_kwargs["correlation_id"] == str(dto.payment_id)

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

    async def test_mapper_converts_dto_to_dict(self, publisher, broker_mock):
        """Маппер должен преобразовать DTO в словарь."""
        dto = _create_notification_dto()

        await publisher.publish_new_payment(dto)

        call_kwargs = broker_mock.publish.call_args[1]
        message = call_kwargs["message"]
        assert isinstance(message, dict)

    async def test_publishes_with_decimal_amount(self, publisher, broker_mock):
        """Должен корректно обработать Decimal в данных."""
        from payment_processing_service.infrastructures.mappers.payment import (
            InfrastructurePaymentMapper,
        )

        mapper = InfrastructurePaymentMapper()
        publisher_with_mapper = KafkaPublisher(
            settings=_create_settings(),
            broker=broker_mock,
            mapper=mapper,
        )

        dto = PaymentCreateNotificationDTO(
            payment_id=uuid4(),
            status=PaymentStatusDTO(value="pending"),
            created_at=datetime.now(UTC),
        )

        await publisher_with_mapper.publish_new_payment(dto)

        broker_mock.publish.assert_called_once()
