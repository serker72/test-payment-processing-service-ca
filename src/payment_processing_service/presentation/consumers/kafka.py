import asyncio
import sys
from collections import defaultdict
from typing import Any, Dict

from dishka import AsyncContainer, make_async_container
from dishka_faststream import FastStreamProvider, FromDishka, setup_dishka
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import KafkaMessage
from faststream.middlewares.acknowledgement.config import AckPolicy
from faststream.rabbit.annotations import RabbitMessage
from loguru import logger

from payment_processing_service.application.use_cases.process_payment import ProcessPaymentUseCase
from payment_processing_service.config import constants as c
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.ioc.di import get_providers

container: AsyncContainer = make_async_container(*(get_providers() + [FastStreamProvider()]))
settings = container.get_sync(Settings)

log_level = "DEBUG" if settings.app.backend_debug is True else "INFO"
logger.remove()
logger.add(sys.stderr, format=c.FORMAT_LOG_CONSUMER, level=log_level)
log_extra = {"message_id": "-"}
logger.configure(extra=log_extra)

logger.debug(f"kafka_broker_url: {settings.kafka_broker_url}")
broker = KafkaBroker(settings.kafka_broker_url)
setup_dishka(container, broker=broker, auto_inject=True)
message_retries = defaultdict(int)


@broker.subscriber(
    settings.consumer.consumer_queue_name,
    group_id=f"{settings.consumer.consumer_queue_name}.group_id",
    ack_policy=AckPolicy.MANUAL,
)
async def payment_new_handler(
    message: Dict[str, Any], raw_message: KafkaMessage, use_case: FromDishka[ProcessPaymentUseCase]
) -> None:
    """Обработка события в очереди Kafka `payments.new`"""
    with logger.contextualize(message_id=message.get("payment_id")):
        is_success = await use_case(message)
        retries = message_retries.get(raw_message.correlation_id, 0)
        if is_success:
            await raw_message.ack()
            if message_retries.get(raw_message.correlation_id, 0):
                del message_retries[raw_message.correlation_id]
        else:
            retries += 1
            message_retries[raw_message.correlation_id] = retries
            if retries >= settings.consumer.consumer_queue_delivery_limit:
                if message_retries.get(raw_message.correlation_id, 0):
                    del message_retries[raw_message.correlation_id]

                await broker.publish(
                    message=message,
                    topic=settings.consumer.consumer_dlq_queue_name,
                    correlation_id=raw_message.correlation_id,
                )
                await raw_message.reject()
            else:
                await raw_message.nack()


@broker.subscriber(
    settings.consumer.consumer_dlq_queue_name, group_id=f"{settings.consumer.consumer_dlq_queue_name}.group_id"
)
async def payment_new_dlq_handler(message: Dict[str, Any]) -> None:
    """Обработка события в очереди Kafka `payments.new.dlq`"""
    logger.debug(f"Message: {message.get('payment_id')}\n{repr(message)}")


async def run_consumer() -> None:
    """Запуск потребителя"""
    logger.info("Consumer starting...")
    await broker.start()
    logger.info("Consumer started")

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Main task keyboard interrupt")
    finally:
        logger.info("Consumer shutdowning...")
        await broker.stop()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(run_consumer())
