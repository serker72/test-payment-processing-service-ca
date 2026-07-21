import random
from dataclasses import dataclass
from typing import final

from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentDTO
from payment_processing_service.application.exceptions import FailedPublishPaymentMessageBrokerException
from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.message_broker import PaymentMessageBrokerPublisherProtocol
from payment_processing_service.infrastructures.broker.kafka import KafkaPublisher
from payment_processing_service.infrastructures.broker.rabbit import RabbitPublisher


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PublishPaymentToBrokerUseCase:
    """Сценарий публикации уведомления о приёме платежа в брокере сообщений."""

    # message_broker: PaymentMessageBrokerPublisherProtocol
    message_rabbit_broker: RabbitPublisher
    message_kafka_broker: KafkaPublisher
    payment_mapper: DtoPaymentEntityMapperProtocol

    async def __call__(self, payment_dto: PaymentDTO) -> None:
        """Выполняет сценарий публикации уведомления о приёме платежа в брокере сообщений."""
        message_brokers = [self.message_rabbit_broker, self.message_kafka_broker]
        # message_broker = random.choice(message_brokers)
        message_broker = message_brokers[random.randint(0, len(message_brokers) - 1)]

        try:
            notification_dto = self.payment_mapper.to_notification_dto(payment_dto)
            # await self.message_broker.publish_new_payment(notification_dto)
            await message_broker.publish_new_payment(notification_dto)
            logger.info(
                f"Published new payment event to message broker {message_broker.broker.__class__.__name__}, "
                f"id={payment_dto.id}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to publish payment notification to message broker {message_broker.broker.__class__.__name__} "
                f"(non-critical), id={payment_dto.id}, error={str(e)}"
            )
            raise FailedPublishPaymentMessageBrokerException("Failed to publish message to broker", str(e)) from e
