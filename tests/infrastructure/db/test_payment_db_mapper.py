"""Тесты для PaymentDBMapper."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus
from payment_processing_service.infrastructures.db.mappers.payment_db_mapper import PaymentDBMapper
from payment_processing_service.infrastructures.db.models.payment import PaymentModel


@pytest.mark.unit
def _create_entity() -> PaymentEntity:
    """Создаёт PaymentEntity для тестов."""
    return PaymentEntity(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=Currency(value=CurrencyEnum.RUB),
        description="Test payment description",
        meta_data=PaymentMetaData(
            address="4276540000000001",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        ),
        status=PaymentStatus(value=PaymentStatusEnum.pending),
        idempotency_key="test-idempotency-key-123",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        processing_error_message=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _create_model() -> PaymentModel:
    """Создаёт PaymentModel для тестов."""
    return PaymentModel(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyEnum.RUB,
        description="Test payment description",
        meta_data={
            "address": "4276540000000001",
            "fio": "Ivan Ivanov",
            "exp_date": "12/25",
            "bank": "Sberbank",
            "phone": "+79001234567",
        },
        status=PaymentStatusEnum.pending,
        idempotency_key="test-idempotency-key-123",
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
        processing_error_message=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestPaymentDBMapper:
    """Тесты для PaymentDBMapper."""

    def setup_method(self):
        self.mapper = PaymentDBMapper()

    def test_to_entity_from_model(self):
        """Должен корректно преобразовывать Model в Entity."""
        model = _create_model()
        entity = self.mapper.to_entity(model)

        assert isinstance(entity, PaymentEntity)
        assert entity.id == model.id
        assert entity.amount == model.amount
        assert entity.currency.value == CurrencyEnum.RUB
        assert entity.description == model.description
        assert entity.meta_data.address == model.meta_data["address"]
        assert entity.meta_data.fio == model.meta_data["fio"]
        assert entity.meta_data.exp_date == model.meta_data["exp_date"]
        assert entity.meta_data.bank == model.meta_data["bank"]
        assert entity.meta_data.phone == model.meta_data["phone"]
        assert entity.status.value == PaymentStatusEnum.pending
        assert entity.idempotency_key == model.idempotency_key
        assert entity.webhook_url == model.webhook_url
        assert entity.expired_at == model.expired_at
        assert entity.processing_error_message == model.processing_error_message

    def test_to_model_from_entity(self):
        """Должен корректно преобразовывать Entity в Model."""
        entity = _create_entity()
        model = self.mapper.to_model(entity)

        assert isinstance(model, PaymentModel)
        assert model.id == entity.id
        assert model.amount == entity.amount
        assert model.currency == CurrencyEnum.RUB
        assert model.description == entity.description
        assert model.meta_data["address"] == entity.meta_data.address
        assert model.meta_data["fio"] == entity.meta_data.fio
        assert model.meta_data["exp_date"] == entity.meta_data.exp_date
        assert model.meta_data["bank"] == entity.meta_data.bank
        assert model.meta_data["phone"] == entity.meta_data.phone
        assert model.status == PaymentStatusEnum.pending
        assert model.idempotency_key == entity.idempotency_key
        assert model.webhook_url == entity.webhook_url
        assert model.expired_at == entity.expired_at
        assert model.processing_error_message == entity.processing_error_message

    def test_roundtrip_entity_to_model_to_entity(self):
        """Циклическое преобразование Entity -> Model -> Entity должно быть идентичным."""
        entity = _create_entity()
        model = self.mapper.to_model(entity)
        restored_entity = self.mapper.to_entity(model)

        assert restored_entity.id == entity.id
        assert restored_entity.amount == entity.amount
        assert restored_entity.currency.value == entity.currency.value
        assert restored_entity.description == entity.description
        assert restored_entity.meta_data.address == entity.meta_data.address
        assert restored_entity.status.value == entity.status.value
        assert restored_entity.idempotency_key == entity.idempotency_key

    def test_to_model_handles_null_webhook(self):
        """Должен корректно обрабатывать None webhook_url при преобразовании в Model."""
        entity = _create_entity()
        entity_with_none = PaymentEntity(
            id=uuid4(),
            amount=Decimal("100"),
            currency=Currency(value=CurrencyEnum.USD),
            description="No webhook",
            meta_data=PaymentMetaData(address="123", fio="Test"),
            status=PaymentStatus(value=PaymentStatusEnum.failed),
            idempotency_key="key",
            webhook_url=None,
            expired_at=datetime.now(timezone.utc),
        )
        model = self.mapper.to_model(entity_with_none)
        assert model.webhook_url is None

    def test_to_model_handles_null_error_message(self):
        """Должен корректно обрабатывать None processing_error_message."""
        entity = _create_entity()
        model = self.mapper.to_model(entity)
        assert model.processing_error_message is None

    def test_to_entity_handles_null_optional_fields(self):
        """to_entity должен корректно обрабатывать null поля."""
        model = _create_model()
        model.webhook_url = None
        model.processing_error_message = None
        entity = self.mapper.to_entity(model)
        assert entity.webhook_url is None
        assert entity.processing_error_message is None
