from dataclasses import dataclass
from typing import final

from faststream.kafka import KafkaBroker
from loguru import logger

from payment_processing_service.application.dtos.payment import PaymentCreateNotificationDTO
from payment_processing_service.application.interfaces.message_broker import PaymentMessageBrokerPublisherProtocol
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KafkaPublisher(PaymentMessageBrokerPublisherProtocol):
    """Kafka реализация протокола PaymentMessageBrokerPublisherProtocol."""

    settings: Settings
    broker: KafkaBroker
    mapper: InfrastructurePaymentMapper

    async def publish_new_payment(self, notification_dto: PaymentCreateNotificationDTO) -> None:
        """Публикует новое уведомление о приёме платежей в брокере Kafka."""
        try:
            data = self.mapper.to_notification_dict(notification_dto)
            await self.broker.publish(
                message=data,
                topic=self.settings.consumer.consumer_queue_name,
                correlation_id=data["payment_id"],
            )
        except Exception as e:
            logger.error(f"Failed to publish payment: {str(e)}")
            raise
