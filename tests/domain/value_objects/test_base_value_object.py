"""Тесты для value object BaseStringValueObject."""

import pytest

from payment_processing_service.domain.exceptions import InvalidValueException
from payment_processing_service.domain.value_objects.base import BaseStringValueObject


@pytest.mark.unit
class _TestStringValueObject(BaseStringValueObject):
    """Тестовый подкласс с допустимыми значениями."""

    _allowed_values = {"test", "valid", "example"}


class TestStringValueObject:
    """Тесты базового value object для строковых значений."""

    def test_valid_value_creation(self):
        """Должен создавать экземпляр с допустимым значением."""
        obj = _TestStringValueObject(value="test")
        assert obj.value == "test"

    def test_str_representation(self):
        """Должен возвращать строковое представление значения."""
        obj = _TestStringValueObject(value="valid")
        assert str(obj) == "valid"

    def test_allowed_values_property(self):
        """Должен возвращать множество допустимых значений."""
        obj = _TestStringValueObject(value="test")
        assert isinstance(obj.allowed_values, set)

    def test_invalid_value_raises_exception(self):
        """Должен выбрасывать InvalidValueException при недопустимом значении."""
        with pytest.raises(InvalidValueException, match="Invalid value: INVALID"):
            _TestStringValueObject(value="INVALID")

    def test_exception_message_contains_value(self):
        """Сообщение об ошибке должно содержать недопустимое значение."""
        with pytest.raises(InvalidValueException, match="Invalid value: bad_value"):
            _TestStringValueObject(value="bad_value")

    def test_frozen_cannot_modify_value(self):
        """Должен быть неизменяемым (frozen dataclass)."""
        obj = _TestStringValueObject(value="valid")
        with pytest.raises(AttributeError):
            obj.value = "NEW_VALUE"

    def test_ordering(self):
        """Должен поддерживать сравнение (order=True)."""
        a = _TestStringValueObject(value="example")
        b = _TestStringValueObject(value="valid")
        assert a < b

    def test_equality(self):
        """Должен поддерживать равенство."""
        a = _TestStringValueObject(value="test")
        b = _TestStringValueObject(value="test")
        assert a == b

    def test_hashability(self):
        """Должен быть хэшируемым (frozen dataclass)."""
        obj = _TestStringValueObject(value="test")
        assert hash(obj) is not None
