from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.exceptions import FailedPublishPaymentMessageBrokerException
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.message_broker import PaymentMessageBrokerPublisherProtocol


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublishPaymentToBrokerUseCase:
    """Сценарий публикации уведомления о приёме платежа в брокере сообщений."""

    message_broker: PaymentMessageBrokerPublisherProtocol
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, payment_dto: PaymentDTO) -> None:
        """Выполняет сценарий публикации уведомления о приёме платежа в брокере сообщений."""
        try:
            notification_dto = self.payment_mapper.to_notification_dto(payment_dto)
            await self.message_broker.publish_new_payment(notification_dto)
            logger.info(f"Published new payment event to message broker, id={payment_dto.id}")
        except Exception as e:
            logger.warning(
                f"Failed to publish payment notification to message broker (non-critical), "
                f"id={payment_dto.id}, error={str(e)}"
            )
            raise FailedPublishPaymentMessageBrokerException("Failed to publish message to broker", str(e)) from e
