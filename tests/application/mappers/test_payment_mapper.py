"""Тесты для мапперов application layer."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.mappers import PaymentMapper
from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


@pytest.fixture
def payment_entity() -> PaymentEntity:
    """Создаёт PaymentEntity для тестов."""
    return PaymentEntity(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=Currency(value=CurrencyEnum.RUB),
        description="Test payment",
        meta_data=PaymentMetaData(
            address="4276540000000001",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        ),
        status=PaymentStatus(value=PaymentStatusEnum.pending),
        idempotency_key="test-idempotency-key",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        processing_error_message=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def payment_dto(payment_entity: PaymentEntity) -> PaymentDTO:
    """Создаёт PaymentDTO для тестов."""
    return PaymentDTO(
        id=payment_entity.id,
        amount=payment_entity.amount,
        currency=CurrencyDTO(value=payment_entity.currency.value),
        description=payment_entity.description,
        meta_data=PaymentMetaDataDTO(
            address=payment_entity.meta_data.address,
            fio=payment_entity.meta_data.fio,
            exp_date=payment_entity.meta_data.exp_date,
            bank=payment_entity.meta_data.bank,
            phone=payment_entity.meta_data.phone,
        ),
        status=PaymentStatusDTO(value=payment_entity.status.value),
        idempotency_key=payment_entity.idempotency_key,
        webhook_url=payment_entity.webhook_url,
        expired_at=payment_entity.expired_at,
        processing_error_message=payment_entity.processing_error_message,
        created_at=payment_entity.created_at,
        updated_at=payment_entity.updated_at,
    )


class TestPaymentMapper:
    """Тесты для PaymentMapper."""

    @pytest.mark.unit
    def setup_method(self):
        self.mapper = PaymentMapper()

    def test_to_dto_from_entity(self, payment_entity: PaymentEntity, payment_dto: PaymentDTO):
        """Должен корректно преобразовывать Entity в DTO."""
        result = self.mapper.to_dto(payment_entity)
        assert isinstance(result, PaymentDTO)
        assert result.id == payment_dto.id
        assert result.amount == payment_dto.amount
        assert result.currency.value == payment_dto.currency.value
        assert result.description == payment_dto.description
        assert result.meta_data.address == payment_dto.meta_data.address
        assert result.meta_data.fio == payment_dto.meta_data.fio
        assert result.status.value == payment_dto.status.value
        assert result.idempotency_key == payment_dto.idempotency_key
        assert result.webhook_url == payment_dto.webhook_url

    def test_to_entity_from_dto(self, payment_entity: PaymentEntity, payment_dto: PaymentDTO):
        """Должен корректно преобразовывать DTO в Entity."""
        result = self.mapper.to_entity(payment_dto)
        assert isinstance(result, PaymentEntity)
        assert result.id == payment_entity.id
        assert result.amount == payment_entity.amount
        assert result.currency.value == payment_entity.currency.value
        assert result.description == payment_entity.description
        assert result.meta_data.address == payment_entity.meta_data.address
        assert result.meta_data.fio == payment_entity.meta_data.fio
        assert result.meta_data.exp_date == payment_entity.meta_data.exp_date
        assert result.meta_data.bank == payment_entity.meta_data.bank
        assert result.meta_data.phone == payment_entity.meta_data.phone
        assert result.status.value == payment_entity.status.value
        assert result.idempotency_key == payment_entity.idempotency_key

    def test_roundtrip_entity_to_dto_to_entity(self, payment_entity: PaymentEntity):
        """Циклическое преобразование Entity -> DTO -> Entity должно быть идентичным."""
        dto = self.mapper.to_dto(payment_entity)
        restored_entity = self.mapper.to_entity(dto)
        assert restored_entity.id == payment_entity.id
        assert restored_entity.amount == payment_entity.amount
        assert restored_entity.currency.value == payment_entity.currency.value
        assert restored_entity.description == payment_entity.description
        assert restored_entity.status.value == payment_entity.status.value
        assert restored_entity.idempotency_key == payment_entity.idempotency_key

    def test_to_notification_dto(self, payment_entity: PaymentEntity):
        """Должен корректно создавать PaymentCreateNotificationDTO."""
        result = self.mapper.to_notification_dto(payment_entity)
        assert isinstance(result, PaymentCreateNotificationDTO)
        assert result.payment_id == payment_entity.id
        assert result.status.value == payment_entity.status.value
        assert result.created_at == payment_entity.created_at

    def test_to_dto_preserves_optional_fields(self, payment_entity: PaymentEntity):
        """DTO должен сохранять все необязательные поля."""
        entity_with_optional = PaymentEntity(
            amount=Decimal("100"),
            currency=Currency(value=CurrencyEnum.RUB),
            description="Test",
            meta_data=PaymentMetaData(address="123", fio="Test"),
            status=PaymentStatus(value=PaymentStatusEnum.pending),
            idempotency_key="key",
            webhook_url="https://webhook.test",
            expired_at=datetime.now(timezone.utc),
            processing_error_message="Error occurred",
        )
        dto = self.mapper.to_dto(entity_with_optional)
        assert dto.webhook_url == "https://webhook.test"
        assert dto.processing_error_message == "Error occurred"
        assert dto.expired_at is not None

    def test_to_entity_preserves_optional_fields(self, payment_dto: PaymentDTO):
        """Entity должен сохранять все необязательные поля из DTO."""
        entity = self.mapper.to_entity(payment_dto)
        assert entity.webhook_url == payment_dto.webhook_url
        assert entity.processing_error_message == payment_dto.processing_error_message
        assert entity.expired_at == payment_dto.expired_at

    def test_to_dto_empty_optional_fields(self):
        """DTO должен корректно обрабатывать пустые необязательные поля."""
        entity = PaymentEntity(
            amount=Decimal("100"),
            currency=Currency(value=CurrencyEnum.USD),
            description="Test",
            meta_data=PaymentMetaData(address="123", fio="Test"),
            status=PaymentStatus(value=PaymentStatusEnum.failed),
            idempotency_key="key",
            webhook_url=None,
            expired_at=None,
            processing_error_message=None,
        )
        dto = self.mapper.to_dto(entity)
        assert dto.webhook_url is None
        assert dto.processing_error_message is None
        assert dto.expired_at is None

    def test_to_notification_dto_fields(self):
        """Notification DTO должен содержать только нужные поля."""
        entity = PaymentEntity(
            amount=Decimal("100"),
            currency=Currency(value=CurrencyEnum.EUR),
            description="Test",
            meta_data=PaymentMetaData(address="123", fio="Test"),
            status=PaymentStatus(value=PaymentStatusEnum.succeeded),
            idempotency_key="key",
        )
        notification = self.mapper.to_notification_dto(entity)
        assert notification.payment_id == entity.id
        assert notification.status.value == PaymentStatusEnum.succeeded
        assert notification.created_at == entity.created_at
