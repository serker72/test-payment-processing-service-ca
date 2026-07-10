from typing import final


@final
class InvalidValueException(Exception):
    """Исключение возникает при указании недействительного значения."""


@final
class InvalidCurrencyException(Exception):
    """Исключение возникает при указании недействительного значения валюты."""


@final
class InvalidPaymentStatusException(Exception):
    """Исключение возникает при указании недействительного значения статуса платежа."""


@final
class DomainValidationError(Exception):
    """Исключение возникает при неудаче проверки доменной сущности."""


class WebhookDeliveryError(Exception):
    """Исключение возникает при неудачной доставке вебхука после исчерпания всех повторных попыток."""
