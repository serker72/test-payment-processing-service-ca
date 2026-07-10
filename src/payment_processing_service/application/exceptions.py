from typing import final


@final
class PaymentNotFoundError(Exception):
    """Исключение возникает при отсутствии платежа."""


@final
class FailedPublishPaymentMessageBrokerException(Exception):
    """Исключение возникает при неудаче публикации события о создании платежа в брокере сообщений."""
