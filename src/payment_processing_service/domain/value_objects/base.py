from dataclasses import dataclass
from typing import ClassVar, Type

from payment_processing_service.domain.exceptions import InvalidValueException


@dataclass(frozen=True, kw_only=True, order=True)
class BaseStringValueObject:
    """
    Объект, представляющий текстовое значение.

    Гарантирует, что значение является одним из заранее определённых допустимых значений.
    """

    _allowed_values: ClassVar[set[str]] = set()
    _invalid_value_exception_class: ClassVar[Type[Exception]] = InvalidValueException
    _invalid_value_exception_message_template: ClassVar[str] = "Invalid value: {value}"
    value: str

    def __post_init__(self) -> None:
        """
        Валидирует значение после инициализации.

        Raises:
            InvalidCurrencyException: Если указанное значение не разрешено.
        """
        if self.value not in self._allowed_values:
            raise self._invalid_value_exception_class(
                self._invalid_value_exception_message_template.format(value=self.value)
            )

    def __str__(self) -> str:
        """Возвращает строковое представление значения."""
        return self.value

    @property
    def allowed_values(self) -> set[str]:
        """Возвращает список допустимых значений."""
        return self._allowed_values
