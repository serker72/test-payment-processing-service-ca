"""Тесты для use case PublishPaymentToBroker."""

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
from payment_processing_service.application.exceptions import FailedPublishPaymentMessageBrokerException
from payment_processing_service.application.use_cases.publish_payment_to_broker import PublishPaymentToBrokerUseCase


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


class TestPublishPaymentToBrokerUseCase:
    """Тесты для PublishPaymentToBrokerUseCase."""

    @pytest.fixture
    def mock_broker(self):
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_mapper(self):
        mock = MagicMock()
        mock.to_notification_dto = MagicMock()
        return mock

    @pytest.fixture
    def use_case(self, mock_broker, mock_mapper):
        return PublishPaymentToBrokerUseCase(
            message_broker=mock_broker,
            payment_mapper=mock_mapper,
        )

    async def test_publishes_notification(self, use_case, mock_broker, mock_mapper):
        """Должен опубликовать notification в брокер."""
        dto = _create_dto()
        notification = PaymentCreateNotificationDTO(
            payment_id=dto.id,
            status=dto.status,
            created_at=dto.created_at,
        )
        mock_mapper.to_notification_dto.return_value = notification

        await use_case(dto)

        mock_mapper.to_notification_dto.assert_called_once_with(dto)
        mock_broker.publish_new_payment.assert_called_once_with(notification)

    async def test_raises_exception_on_broker_failure(self, use_case, mock_broker, mock_mapper):
        """Должен выбросить исключение при ошибке брокера."""
        dto = _create_dto()
        notification = PaymentCreateNotificationDTO(
            payment_id=dto.id,
            status=dto.status,
            created_at=dto.created_at,
        )
        mock_mapper.to_notification_dto.return_value = notification
        mock_broker.publish_new_payment.side_effect = Exception("Connection refused")

        with pytest.raises(FailedPublishPaymentMessageBrokerException):
            await use_case(dto)

    async def test_mapper_converts_dto_to_notification(self, use_case, mock_broker, mock_mapper):
        """Маппер должен преобразовать DTO в notification DTO."""
        dto = _create_dto()
        notification = PaymentCreateNotificationDTO(
            payment_id=dto.id,
            status=dto.status,
            created_at=dto.created_at,
        )
        mock_mapper.to_notification_dto.return_value = notification

        await use_case(dto)

        mock_mapper.to_notification_dto.assert_called_once_with(dto)
