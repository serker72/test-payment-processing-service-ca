"""Тесты для PaymentPresentationMapper."""

from datetime import UTC, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.presentation.api.rest.v1.mappers.payment_mapper import PaymentPresentationMapper
from payment_processing_service.presentation.api.rest.v1.schemas.common import PaymentMetaDataSchema
from payment_processing_service.presentation.api.rest.v1.schemas.requests import PaymentCreateRequestSchema


def _create_request_schema() -> PaymentCreateRequestSchema:
    """Создаёт PaymentCreateRequestSchema для тестов."""
    return PaymentCreateRequestSchema(
        amount=Decimal("1500.00"),
        currency="RUB",
        description="Test payment",
        meta_data=PaymentMetaDataSchema(
            address="4276540000000001",
            fio="Ivan Ivanov",
            exp_date="12/25",
            bank="Sberbank",
            phone="+79001234567",
        ),
        webhook_url="https://example.com/webhook",
        expired_at=datetime.now(timezone.utc),
    )


def _create_dto() -> PaymentDTO:
    """Создаёт PaymentDTO для тестов."""
    return PaymentDTO(
        id=uuid4(),
        amount=Decimal("1500.00"),
        currency=CurrencyDTO(value="RUB"),
        description="Test payment",
        meta_data=PaymentMetaDataDTO(
            address="4276540000000001",
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


class TestPaymentPresentationMapper:
    """Тесты для PaymentPresentationMapper."""

    @pytest.mark.unit
    def setup_method(self):
        self.mapper = PaymentPresentationMapper()

    def test_from_request_converts_to_dto(self):
        """Должен преобразовывать request schema в DTO."""
        request = _create_request_schema()
        dto = self.mapper.from_request(request)

        assert isinstance(dto, PaymentDTO)
        assert dto.amount == request.amount
        assert dto.currency.value == request.currency
        assert dto.description == request.description
        assert dto.meta_data.address == request.meta_data.address
        assert dto.meta_data.fio == request.meta_data.fio
        assert dto.webhook_url == request.webhook_url
        assert dto.expired_at == request.expired_at

    def test_from_request_generates_uuid(self):
        """from_request должен генерировать UUID для id."""
        request = _create_request_schema()
        dto = self.mapper.from_request(request)

        assert dto.id is not None

    def test_from_request_preserves_meta_data(self):
        """from_request должен сохранять все поля meta_data."""
        request = _create_request_schema()
        dto = self.mapper.from_request(request)

        assert dto.meta_data.address == request.meta_data.address
        assert dto.meta_data.fio == request.meta_data.fio
        assert dto.meta_data.exp_date == request.meta_data.exp_date
        assert dto.meta_data.bank == request.meta_data.bank
        assert dto.meta_data.phone == request.meta_data.phone

    def test_to_response_converts_dto_to_schema(self):
        """Должен преобразовывать DTO в response schema."""
        dto = _create_dto()
        response = self.mapper.to_response(dto)

        assert response.id == dto.id
        assert response.amount == dto.amount
        assert response.currency == str(dto.currency.value)
        assert response.description == dto.description
        assert response.status == str(dto.status.value)
        assert response.idempotency_key == dto.idempotency_key
        assert response.webhook_url == dto.webhook_url
        assert response.expired_at == dto.expired_at
        assert response.created_at == dto.created_at
        assert response.updated_at == dto.updated_at
        assert response.processing_error_message == dto.processing_error_message

    def test_to_response_converts_meta_data(self):
        """to_response должен преобразовывать meta_data."""
        dto = _create_dto()
        response = self.mapper.to_response(dto)

        assert response.meta_data.address == dto.meta_data.address
        assert response.meta_data.fio == dto.meta_data.fio
        assert response.meta_data.exp_date == dto.meta_data.exp_date
        assert response.meta_data.bank == dto.meta_data.bank
        assert response.meta_data.phone == dto.meta_data.phone

    def test_to_create_response_converts_dto(self):
        """Должен преобразовывать DTO в create response schema."""
        dto = _create_dto()
        response = self.mapper.to_create_response(dto)

        assert response.payment_id == str(dto.id)
        assert response.status == str(dto.status.value)
        assert response.created_at == dto.created_at

    def test_roundtrip_request_to_dto_to_response(self):
        """Циклическое преобразование Request -> DTO -> Response."""
        request = _create_request_schema()
        dto = self.mapper.from_request(request)
        response = self.mapper.to_response(dto)

        assert response.amount == request.amount
        assert response.currency == request.currency
        assert response.description == request.description
        assert response.meta_data.address == request.meta_data.address

    def test_to_response_handles_null_webhook_url(self):
        """to_response должен корректно обрабатывать None webhook_url."""
        from dataclasses import replace

        dto = replace(_create_dto(), webhook_url=None)
        response = self.mapper.to_response(dto)
        assert response.webhook_url is None

    def test_to_response_handles_null_error_message(self):
        """to_response должен корректно обрабатывать None processing_error_message."""
        from dataclasses import replace

        dto = replace(_create_dto(), processing_error_message=None)
        response = self.mapper.to_response(dto)
        assert response.processing_error_message is None

    def test_to_create_response_status(self):
        """to_create_response должен корректно преобразовывать статус."""
        dto = _create_dto()
        response = self.mapper.to_create_response(dto)
        assert response.status == "pending"
