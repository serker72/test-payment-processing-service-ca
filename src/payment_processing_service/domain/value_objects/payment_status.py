from dataclasses import dataclass
from typing import ClassVar, final

from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.domain.exceptions import InvalidPaymentStatusException
from payment_processing_service.domain.value_objects.base import BaseStringValueObject


@final
@dataclass(frozen=True, slots=True, kw_only=True, order=True)
class PaymentStatus(BaseStringValueObject):
    """
    Объект, представляющий статус платежа.

    Гарантирует, что значение статуса платежа является одним из заранее определённых допустимых значений.
    """

    _allowed_values: ClassVar[set[str]] = {
        PaymentStatusEnum.pending,
        PaymentStatusEnum.succeeded,
        PaymentStatusEnum.failed,
    }
    _invalid_value_exception_class = InvalidPaymentStatusException
    _invalid_value_exception_message_template = "Invalid payment status: {value}"
    # value: str
    #
    # def __post_init__(self) -> None:
    #     """
    #     Валидирует значение статуса платежа после инициализации.
    #
    #     Raises:
    #         InvalidPaymentStatusException: Если указанное значение статуса платежа не разрешено.
    #     """
    #     if self.value not in self._allowed_values:
    #         raise InvalidPaymentStatusException(f"Invalid payment status: {self.value}")
    #
    # def __str__(self) -> str:
    #     """Возвращает строковое представление статуса платежа."""
    #     return self.value
