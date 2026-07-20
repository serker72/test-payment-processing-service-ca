"""Тесты для доменной сущности PaymentEntity."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.exceptions import DomainValidationError
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus
from tests.conftest import PaymentEntityFactory


@pytest.mark.unit
class TestPaymentMetaData:
    """Тесты для PaymentMetaData."""

    def test_basic_fields(self):
        """Должен создавать метаданные с обязательными полями."""
        meta = PaymentMetaData(address="1234567890123456", fio="Ivan Ivanov")
        assert meta.address == "1234567890123456"
        assert meta.fio == "Ivan Ivanov"

    def test_optional_fields_default_none(self):
        """Должен иметь None для необязательных полей по умолчанию."""
        meta = PaymentMetaData(address="1234567890123456", fio="Ivan Ivanov")
        assert meta.exp_date is None
        assert meta.bank is None
        assert meta.phone is None

    def test_optional_fields_with_values(self):
        """Должен поддерживать заполнение необязательных полей."""
        meta = PaymentMetaData(
            address="1234567890123456",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        )
        assert meta.exp_date == "12/25"
        assert meta.bank == "Sberbank"
        assert meta.phone == "+79001234567"

    def test_frozen(self):
        """Должен быть неизменяемым."""
        meta = PaymentMetaData(address="1234567890123456", fio="Ivan Ivanov")
        with pytest.raises(AttributeError):
            meta.address = "9876543210987654"

    def test_ordering(self):
        """Должен поддерживать сравнение."""
        meta_a = PaymentMetaData(address="AAA", fio="A")
        meta_b = PaymentMetaData(address="BBB", fio="B")
        assert meta_a < meta_b

    def test_equality(self):
        """Должен поддерживать равенство."""
        meta_a = PaymentMetaData(address="123", fio="A")
        meta_b = PaymentMetaData(address="123", fio="A")
        assert meta_a == meta_b


class TestPaymentEntity:
    """Тесты для PaymentEntity."""

    def test_creation_with_defaults(self):
        """Должен создавать сущность с дефолтными значениями."""
        entity = PaymentEntityFactory.build()
        assert entity.id is not None
        assert isinstance(entity.amount, Decimal)
        assert entity.currency.value is not None
        assert entity.description is not None

    def test_creation_with_custom_values(self):
        """Должен создавать сущность с пользовательскими значениями."""
        entity = PaymentEntityFactory.build(
            amount=Decimal("500.50"),
            description="Test payment",
        )
        assert entity.amount == Decimal("500.50")
        assert entity.description == "Test payment"

    def test_id_generated_by_default(self):
        """ID должен генерироваться по умолчанию."""
        entity = PaymentEntityFactory.build()
        assert entity.id is not None

    def test_amount_validation_positive(self):
        """Должен валидировать, что сумма > 0."""
        entity = PaymentEntityFactory.build(amount=Decimal("100.00"))
        assert entity.amount == Decimal("100.00")

    def test_amount_validation_zero_raises(self):
        """Должен выбрасывать DomainValidationError при сумме = 0."""
        with pytest.raises(DomainValidationError, match="Amount must be greater than 0"):
            PaymentEntityFactory.build(amount=Decimal("0"))

    def test_amount_validation_negative_raises(self):
        """Должен выбрасывать DomainValidationError при отрицательной сумме."""
        with pytest.raises(DomainValidationError, match="Amount must be greater than 0"):
            PaymentEntityFactory.build(amount=Decimal("-100.00"))

    def test_frozen(self):
        """Должен быть неизменяемым."""
        entity = PaymentEntityFactory.build()
        with pytest.raises(AttributeError):
            entity.amount = Decimal("999")

    def test_equality(self):
        """Должен поддерживать равенство (по всем полям)."""
        from uuid import uuid4 as gen_uuid

        test_id = gen_uuid()
        test_expired = datetime.now(timezone.utc)
        entity_a = PaymentEntityFactory.build(
            id=test_id,
            amount=Decimal("100"),
            description="Same",
            meta_data=PaymentMetaData(address="123", fio="A"),
            idempotency_key="same-key",
            webhook_url="http://test.com",
            expired_at=test_expired,
        )
        entity_b = PaymentEntityFactory.build(
            id=test_id,
            amount=Decimal("100"),
            description="Same",
            meta_data=PaymentMetaData(address="123", fio="A"),
            idempotency_key="same-key",
            webhook_url="http://test.com",
            expired_at=test_expired,
        )
        assert entity_a.id == entity_b.id
        assert entity_a.amount == entity_b.amount

    def test_all_fields_populated(self):
        """Все поля должны быть заполнены."""
        entity = PaymentEntityFactory.build()
        assert entity.webhook_url is not None
        assert entity.expired_at is not None
        assert entity.idempotency_key is not None
        assert entity.created_at is not None
        assert entity.updated_at is not None
        assert entity.processing_error_message is None

    def test_expired_at_before_now(self):
        """Должен поддерживать expired_at в прошлом."""
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        from dataclasses import replace

        entity = PaymentEntityFactory.build(expired_at=expired)
        assert entity.expired_at == expired
