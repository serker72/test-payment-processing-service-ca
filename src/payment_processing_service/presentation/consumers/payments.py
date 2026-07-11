import asyncio
import sys
from typing import Any, Dict

from dishka import AsyncContainer, make_async_container
from dishka_faststream import FastStreamProvider, FromDishka, setup_dishka
from faststream.middlewares.acknowledgement.config import AckPolicy
from faststream.rabbit import ExchangeType, QueueType, RabbitBroker, RabbitExchange, RabbitQueue
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

broker = RabbitBroker(settings.broker_url)
setup_dishka(container, broker=broker, auto_inject=True)

payment_exchange = RabbitExchange(settings.consumer.consumer_exchange_name, type=ExchangeType.TOPIC, durable=True)
dlx_exchange = RabbitExchange(settings.consumer.consumer_dlx_exchange_name, type=ExchangeType.FANOUT, durable=True)

payment_queue = RabbitQueue(
    settings.consumer.consumer_queue_name,
    queue_type=QueueType.QUORUM,
    durable=True,
    routing_key=settings.consumer.consumer_payment_routing_key,
    arguments={
        "x-queue-type": "quorum",
        "x-overflow": "reject-publish",
        "x-dead-letter-exchange": settings.consumer.consumer_dlx_exchange_name,
        "x-dead-letter-routing-key": settings.consumer.consumer_dead_letter_routing_key,
        "x-delivery-limit": settings.consumer.consumer_queue_delivery_limit,
        "x-dead-letter-strategy": "at-least-once",
    },
)

dlq_queue = RabbitQueue(
    settings.consumer.consumer_dlq_queue_name,
    durable=True,
    queue_type=QueueType.QUORUM,
    routing_key=settings.consumer.consumer_dead_letter_routing_key,
    arguments={
        "x-queue-type": "quorum",
        "x-message-ttl": settings.consumer.consumer_dlq_queue_message_ttl,
    },
)


@broker.subscriber(queue=payment_queue, exchange=payment_exchange, ack_policy=AckPolicy.NACK_ON_ERROR)
async def payment_new_handler(
    message: Dict[str, Any],
    raw_message: RabbitMessage,
    use_case: FromDishka[ProcessPaymentUseCase],
) -> None:
    """Обработка события в очереди RabbitMQ `payments.new`"""
    with logger.contextualize(message_id=raw_message.message_id):
        return await use_case(message)


@broker.subscriber(queue=dlq_queue, exchange=dlx_exchange)
async def payment_new_dlq_handler(message: Dict[str, Any], raw_message: RabbitMessage) -> None:
    """Обработка события в очереди RabbitMQ `payments.new.dlq`"""
    logger.debug(f"Message: {raw_message.message_id}\n{repr(raw_message.headers)}\n{repr(message)}")


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
