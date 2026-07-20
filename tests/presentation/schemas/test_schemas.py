"""Тесты для Pydantic схем API."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from payment_processing_service.presentation.api.rest.v1.schemas.common import (
    PaymentBaseSchema,
    PaymentMetaDataSchema,
)
from payment_processing_service.presentation.api.rest.v1.schemas.requests import PaymentCreateRequestSchema
from payment_processing_service.presentation.api.rest.v1.schemas.responses import (
    PaymentCreateResponseSchema,
    PaymentResponseSchema,
)


@pytest.mark.unit
class TestPaymentMetaDataSchema:
    """Тесты для PaymentMetaDataSchema."""

    def test_valid_metadata(self):
        """Должен создавать схему с валидными данными."""
        meta = PaymentMetaDataSchema(
            address="1234567890123456",
            fio="Ivan Ivanov",
        )
        assert meta.address == "1234567890123456"
        assert meta.fio == "Ivan Ivanov"
        assert meta.exp_date is None
        assert meta.bank is None
        assert meta.phone is None

    def test_metadata_with_all_fields(self):
        """Должен создавать схему со всеми полями."""
        meta = PaymentMetaDataSchema(
            address="1234567890123456",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        )
        assert meta.exp_date == "12/25"
        assert meta.bank == "Sberbank"
        assert meta.phone == "+79001234567"

    def test_missing_required_address(self):
        """Должен выбрасывать ValidationError при отсутствии address."""
        with pytest.raises(ValidationError):
            PaymentMetaDataSchema(fio="Ivan Ivanov")


class TestPaymentBaseSchema:
    """Тесты для PaymentBaseSchema."""

    def test_valid_base_schema(self):
        """Должен создавать схему с валидными данными."""
        schema = PaymentBaseSchema(
            amount=Decimal("1500.00"),
            currency="RUB",
            description="Test payment",
            meta_data=PaymentMetaDataSchema(address="1234567890123456", fio="Ivan Ivanov"),
        )
        assert schema.amount == Decimal("1500.00")
        assert schema.currency == "RUB"
        assert schema.description == "Test payment"

    def test_optional_fields_default_none(self):
        """Необязательные поля должны быть None по умолчанию."""
        schema = PaymentBaseSchema(
            amount=Decimal("100"),
            currency="USD",
            description="Test",
            meta_data=PaymentMetaDataSchema(address="123", fio="Test"),
        )
        assert schema.webhook_url is None
        assert schema.expired_at is None
        assert schema.status is None
        assert schema.idempotency_key is None

    def test_all_optional_fields(self):
        """Должен поддерживать все необязательные поля."""
        expired = datetime.now(timezone.utc)
        schema = PaymentBaseSchema(
            amount=Decimal("100"),
            currency="EUR",
            description="Full test",
            meta_data=PaymentMetaDataSchema(address="123", fio="Test"),
            webhook_url="https://example.com/webhook",
            expired_at=expired,
            status="pending",
            idempotency_key="test-key",
        )
        assert schema.webhook_url == "https://example.com/webhook"
        assert schema.expired_at == expired
        assert schema.status == "pending"
        assert schema.idempotency_key == "test-key"


class TestPaymentCreateRequestSchema:
    """Тесты для PaymentCreateRequestSchema."""

    def test_valid_create_request(self):
        """Должен создавать схему запроса с валидными данными."""
        schema = PaymentCreateRequestSchema(
            amount=Decimal("1500.00"),
            currency="RUB",
            description="Test payment",
            meta_data=PaymentMetaDataSchema(
                address="1234567890123456",
                fio="Ivan Ivanov",
            ),
        )
        assert schema.amount == Decimal("1500.00")
        assert schema.currency == "RUB"
        assert schema.status is None
        assert schema.idempotency_key is None


class TestPaymentResponseSchema:
    """Тесты для PaymentResponseSchema."""

    def test_valid_response(self):
        """Должен создавать схему ответа с валидными данными."""
        now = datetime.now(timezone.utc)
        schema = PaymentResponseSchema(
            id=uuid4(),
            amount=Decimal("1500.00"),
            currency="RUB",
            description="Test payment",
            meta_data=PaymentMetaDataSchema(address="123", fio="Test"),
            status="succeeded",
            idempotency_key="test-key",
            created_at=now,
            updated_at=now,
        )
        assert schema.amount == Decimal("1500.00")
        assert schema.status == "succeeded"

    def test_optional_error_message(self):
        """processing_error_message может быть None."""
        now = datetime.now(timezone.utc)
        schema = PaymentResponseSchema(
            id=uuid4(),
            amount=Decimal("100"),
            currency="USD",
            description="Test",
            meta_data=PaymentMetaDataSchema(address="123", fio="Test"),
            status="failed",
            idempotency_key="key",
            created_at=now,
            processing_error_message="Insufficient funds",
        )
        assert schema.processing_error_message == "Insufficient funds"


class TestPaymentCreateResponseSchema:
    """Тесты для PaymentCreateResponseSchema."""

    def test_valid_create_response(self):
        """Должен создавать схему ответа с валидными данными."""
        now = datetime.now(timezone.utc)
        schema = PaymentCreateResponseSchema(
            payment_id="123e4567-e89b-12d3-a456-426614174000",
            status="pending",
            created_at=now,
        )
        assert schema.payment_id == "123e4567-e89b-12d3-a456-426614174000"
        assert schema.status == "pending"

    def test_missing_payment_id(self):
        """Должен выбрасывать ValidationError при отсутствии payment_id."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            PaymentCreateResponseSchema(
                status="pending",
                created_at=now,
            )
