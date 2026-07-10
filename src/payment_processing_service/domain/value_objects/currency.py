from dataclasses import dataclass
from typing import ClassVar, final

from payment_processing_service.config.enums import CurrencyEnum
from payment_processing_service.domain.exceptions import InvalidCurrencyException
from payment_processing_service.domain.value_objects.base import BaseStringValueObject


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class Currency(BaseStringValueObject):
    """
    Объект, представляющий валюту.

    Гарантирует, что значение валюты является одним из заранее определённых допустимых значений.
    """

    _allowed_values = {CurrencyEnum.RUB, CurrencyEnum.USD, CurrencyEnum.EUR}
    _invalid_value_exception_class = InvalidCurrencyException
    _invalid_value_exception_message_template = "Invalid currency: {value}"
    # value: str
    #
    # def __post_init__(self) -> None:
    #     """
    #     Валидирует значение валюты после инициализации.
    #
    #     Raises:
    #         InvalidCurrencyException: Если указанное значение валюты не разрешено.
    #     """
    #     if self.value not in self._allowed_values:
    #         raise InvalidCurrencyException(f"Invalid currency: {self.value}")
    #
    # def __str__(self) -> str:
    #     """Возвращает строковое представление валюты."""
    #     return self.value
    #
    # @property
    # def allowed_values(self) -> set[str]:
    #     """Возвращает список допустимых значений"""
    #     return self._allowed_values
