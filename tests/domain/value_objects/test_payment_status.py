"""Тесты для value object PaymentStatus."""

import pytest

from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.domain.exceptions import InvalidPaymentStatusException
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


@pytest.mark.unit
class TestPaymentStatus:
    """Тесты для value object PaymentStatus."""

    def test_valid_pending_status(self):
        """Должен создавать pending статус."""
        status = PaymentStatus(value=PaymentStatusEnum.pending)
        assert status.value == PaymentStatusEnum.pending

    def test_valid_succeeded_status(self):
        """Должен создавать succeeded статус."""
        status = PaymentStatus(value=PaymentStatusEnum.succeeded)
        assert status.value == PaymentStatusEnum.succeeded

    def test_valid_failed_status(self):
        """Должен создавать failed статус."""
        status = PaymentStatus(value=PaymentStatusEnum.failed)
        assert status.value == PaymentStatusEnum.failed

    def test_invalid_status_raises_exception(self):
        """Должен выбрасывать InvalidPaymentStatusException при недопустимом статусе."""
        with pytest.raises(InvalidPaymentStatusException, match="Invalid payment status: cancelled"):
            PaymentStatus(value="cancelled")

    def test_invalid_status_message_contains_value(self):
        """Сообщение об ошибке должно содержать недопустимое значение."""
        with pytest.raises(InvalidPaymentStatusException, match="Invalid payment status: unknown"):
            PaymentStatus(value="unknown")

    def test_allowed_values(self):
        """Должен иметь корректное множество допустимых значений."""
        status = PaymentStatus(value=PaymentStatusEnum.pending)
        assert status.allowed_values == {
            PaymentStatusEnum.pending,
            PaymentStatusEnum.succeeded,
            PaymentStatusEnum.failed,
        }

    def test_str_representation(self):
        """Должен возвращать строковое представление."""
        status = PaymentStatus(value=PaymentStatusEnum.succeeded)
        assert str(status) == PaymentStatusEnum.succeeded

    def test_frozen_cannot_modify(self):
        """Должен быть неизменяемым."""
        status = PaymentStatus(value=PaymentStatusEnum.pending)
        with pytest.raises(AttributeError):
            status.value = "NEW"

    def test_ordering(self):
        """Должен поддерживать сравнение."""
        pending = PaymentStatus(value=PaymentStatusEnum.pending)
        succeeded = PaymentStatus(value=PaymentStatusEnum.succeeded)
        failed = PaymentStatus(value=PaymentStatusEnum.failed)
        # Status values are StrEnum, comparing by their string representation
        # 'failed' < 'pending' < 'succeeded' alphabetically
        assert str(failed.value) < str(pending.value) < str(succeeded.value)

    def test_equality(self):
        """Должен поддерживать равенство."""
        a = PaymentStatus(value=PaymentStatusEnum.pending)
        b = PaymentStatus(value=PaymentStatusEnum.pending)
        assert a == b

    def test_hashability(self):
        """Должен быть хэшируемым."""
        status = PaymentStatus(value=PaymentStatusEnum.failed)
        statuses = {status, PaymentStatus(value=PaymentStatusEnum.failed)}
        assert len(statuses) == 1
