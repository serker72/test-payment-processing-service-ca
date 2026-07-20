"""Тесты для InfrastructurePaymentMapper."""

from datetime import datetime, timezone
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
        processing_error_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _create_notification_dto() -> PaymentCreateNotificationDTO:
    """Создаёт PaymentCreateNotificationDTO для тестов."""
    return PaymentCreateNotificationDTO(
        payment_id=uuid4(),
        status=PaymentStatusDTO(value="pending"),
        created_at=datetime.now(timezone.utc),
    )


class TestInfrastructurePaymentMapper:
    """Тесты для InfrastructurePaymentMapper."""

    def setup_method(self):
        self.mapper = InfrastructurePaymentMapper()

    def test_to_dict_converts_dto_to_dict(self):
        """Должен преобразовывать PaymentDTO в словарь."""
        dto = _create_dto()
        result = self.mapper.to_dict(dto)

        assert isinstance(result, dict)
        assert result["id"] == str(dto.id)
        assert isinstance(result["amount"], float)
        assert result["amount"] == 1500.0
        assert result["currency"] == {"value": "RUB"}
        assert result["description"] == dto.description
        assert result["meta_data"]["address"] == dto.meta_data.address
        assert result["meta_data"]["fio"] == dto.meta_data.fio
        assert result["status"] == {"value": "pending"}
        assert result["idempotency_key"] == dto.idempotency_key
        assert result["webhook_url"] == dto.webhook_url

    def test_to_dict_converts_expired_at_to_iso(self):
        """Должен преобразовывать expired_at в ISO-строку."""
        dto = _create_dto()
        result = self.mapper.to_dict(dto)

        assert "expired_at" in result
        assert isinstance(result["expired_at"], str)

    def test_to_dict_converts_created_at_to_iso(self):
        """Должен преобразовывать created_at в ISO-строку."""
        dto = _create_dto()
        result = self.mapper.to_dict(dto)

        assert "created_at" in result
        assert isinstance(result["created_at"], str)

    def test_to_dict_converts_updated_at_to_iso(self):
        """Должен преобразовывать updated_at в ISO-строку."""
        dto = _create_dto()
        result = self.mapper.to_dict(dto)

        assert "updated_at" in result
        assert isinstance(result["updated_at"], str)

    def test_to_dict_handles_null_webhook_url(self):
        """Должен корректно обрабатывать None webhook_url."""
        from dataclasses import replace

        dto = replace(_create_dto(), webhook_url=None)
        result = self.mapper.to_dict(dto)

        assert result["webhook_url"] is None

    def test_to_dict_handles_null_processing_error(self):
        """Должен корректно обрабатывать None processing_error_message."""
        from dataclasses import replace

        dto = replace(_create_dto(), processing_error_message=None)
        result = self.mapper.to_dict(dto)

        assert result["processing_error_message"] is None

    def test_from_dict_converts_dict_to_dto(self):
        """Должен преобразовывать словарь в PaymentDTO."""
        dto = _create_dto()
        data = self.mapper.to_dict(dto)
        restored = self.mapper.from_dict(data)

        assert restored.id == dto.id
        assert restored.amount == dto.amount
        assert restored.currency.value == dto.currency.value
        assert restored.description == dto.description
        assert restored.meta_data.address == dto.meta_data.address
        assert restored.status.value == dto.status.value
        assert restored.idempotency_key == dto.idempotency_key

    def test_roundtrip_dict_to_dto_to_dict(self):
        """Циклическое преобразование DTO -> dict -> DTO должно быть идентичным."""
        dto = _create_dto()
        data = self.mapper.to_dict(dto)
        restored = self.mapper.from_dict(data)
        restored_data = self.mapper.to_dict(restored)

        assert restored_data["id"] == data["id"]
        assert restored_data["amount"] == data["amount"]
        assert restored_data["currency"] == data["currency"]
        assert restored_data["description"] == data["description"]
        assert restored_data["status"] == data["status"]

    def test_to_notification_dict(self):
        """Должен преобразовывать PaymentCreateNotificationDTO в словарь."""
        dto = _create_notification_dto()
        result = self.mapper.to_notification_dict(dto)

        assert isinstance(result, dict)
        assert result["payment_id"] == str(dto.payment_id)
        assert result["status"] == {"value": "pending"}
        assert isinstance(result["created_at"], str)

    def test_from_dict_handles_null_optional_fields(self):
        """Должен корректно обрабатывать null поля при десериализации."""
        data = {
            "id": str(uuid4()),
            "amount": 100.0,
            "currency": {"value": "USD"},
            "description": "Test",
            "meta_data": {
                "address": "123",
                "fio": "Test",
                "exp_date": None,
                "bank": None,
                "phone": None,
            },
            "status": {"value": "failed"},
            "idempotency_key": "key",
            "webhook_url": None,
            "expired_at": datetime.now(timezone.utc).isoformat(),
            "processing_error_message": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        dto = self.mapper.from_dict(data)

        assert dto.webhook_url is None
        assert dto.processing_error_message is None
        assert dto.meta_data.exp_date is None
        assert dto.meta_data.bank is None
        assert dto.meta_data.phone is None
