"""Тесты для value object Currency."""

import pytest

from payment_processing_service.config.enums import CurrencyEnum
from payment_processing_service.domain.exceptions import InvalidCurrencyException
from payment_processing_service.domain.value_objects.currency import Currency


@pytest.mark.unit
class TestCurrency:
    """Тесты для value object Currency."""

    def test_valid_rub_currency(self):
        """Должен создавать RUB валюту."""
        currency = Currency(value=CurrencyEnum.RUB)
        assert currency.value == CurrencyEnum.RUB

    def test_valid_usd_currency(self):
        """Должен создавать USD валюту."""
        currency = Currency(value=CurrencyEnum.USD)
        assert currency.value == CurrencyEnum.USD

    def test_valid_eur_currency(self):
        """Должен создавать EUR валюту."""
        currency = Currency(value=CurrencyEnum.EUR)
        assert currency.value == CurrencyEnum.EUR

    def test_invalid_currency_raises_exception(self):
        """Должен выбрасывать InvalidCurrencyException при недопустимой валюте."""
        with pytest.raises(InvalidCurrencyException, match="Invalid currency: BTC"):
            Currency(value="BTC")

    def test_invalid_currency_message_contains_value(self):
        """Сообщение об ошибке должно содержать недопустимое значение."""
        with pytest.raises(InvalidCurrencyException, match="Invalid currency: XYZ"):
            Currency(value="XYZ")

    def test_allowed_values(self):
        """Должен иметь корректное множество допустимых значений."""
        currency = Currency(value=CurrencyEnum.RUB)
        assert currency.allowed_values == {CurrencyEnum.RUB, CurrencyEnum.USD, CurrencyEnum.EUR}

    def test_str_representation(self):
        """Должен возвращать строковое представление."""
        currency = Currency(value=CurrencyEnum.RUB)
        assert str(currency) == CurrencyEnum.RUB

    def test_frozen_cannot_modify(self):
        """Должен быть неизменяемым."""
        currency = Currency(value=CurrencyEnum.USD)
        with pytest.raises(AttributeError):
            currency.value = "NEW"

    def test_ordering(self):
        """Должен поддерживать сравнение."""
        eur = Currency(value=CurrencyEnum.EUR)
        rub = Currency(value=CurrencyEnum.RUB)
        usd = Currency(value=CurrencyEnum.USD)
        assert eur < rub < usd

    def test_equality(self):
        """Должен поддерживать равенство."""
        a = Currency(value=CurrencyEnum.RUB)
        b = Currency(value=CurrencyEnum.RUB)
        assert a == b

    def test_hashability(self):
        """Должен быть хэшируемым."""
        currency = Currency(value=CurrencyEnum.EUR)
        currencies = {currency, Currency(value=CurrencyEnum.EUR), Currency(value=CurrencyEnum.RUB)}
        assert len(currencies) == 2
