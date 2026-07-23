import asyncio
import sys
from typing import Any, Dict

from dishka import AsyncContainer, make_async_container
from dishka_faststream import FastStreamProvider, FromDishka, setup_dishka
from faststream.confluent import KafkaBroker
from faststream.confluent.annotations import KafkaMessage
from faststream.middlewares.acknowledgement.config import AckPolicy
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


@broker.subscriber(
    settings.consumer.consumer_queue_name,
    group_id=f"{settings.consumer.consumer_queue_name}.group_id",
    ack_policy=AckPolicy.MANUAL,
)
async def payment_new_handler(
    message: Dict[str, Any], raw_message: KafkaMessage, use_case: FromDishka[ProcessPaymentUseCase]
) -> None:
    """Обработка события в очереди Kafka `payments.new`

    Механизм retry с exponential backoff:
    - 1-я повторная попытка: задержка 0s (сразу)
    - 2-я повторная попытка: задержка 1s
    - 3-я повторная попытка: задержка 2s
    - После 3 неудачных попыток: сообщение перенаправляется в DLQ
    """
    message_id = message.get("payment_id", "-")
    correlation_id = raw_message.correlation_id

    with logger.contextualize(message_id=message_id):
        try:
            is_success = await use_case(message)
        except Exception as e:
            logger.exception(f"Payment processing failed with exception, payment_id={message_id}, error={e}")
            is_success = False

        retries = raw_message.headers.get("x-retry-count", 0)

        if is_success:
            await raw_message.ack()
            if retries:
                logger.info(f"Payment successfully processed after {retries} retry/retries, payment_id={message_id}")
        else:
            retries += 1
            logger.warning(
                f"Payment processing failed, payment_id={message_id}, attempt={retries}/{settings.consumer.consumer_queue_delivery_limit}"
            )

            if retries >= settings.consumer.consumer_queue_delivery_limit:
                try:
                    await broker.publish(
                        message=message,
                        topic=settings.consumer.consumer_dlq_queue_name,
                        headers={"x-retry-count": str(retries), "x-failed-at": str(retries)},
                        correlation_id=correlation_id,
                    )
                    await raw_message.ack()
                    logger.info(
                        f"Payment moved to DLQ after {retries} attempts, payment_id={message_id}, dlq={settings.consumer.consumer_dlq_queue_name}"
                    )
                except Exception as e:
                    logger.critical(
                        f"Failed to publish to DLQ, payment_id={message_id}, error={e}. Message will be requeued."
                    )
                    await raw_message.nack()
            else:
                # Exponential backoff: 2^(retries-1) seconds, capped at 32s
                delay = min(2 ** (retries - 1), 32)
                logger.info(f"Scheduling requeue with {delay}s delay, payment_id={message_id}, attempt={retries}")
                await asyncio.sleep(delay)
                await raw_message.nack()


@broker.subscriber(
    settings.consumer.consumer_dlq_queue_name, group_id=f"{settings.consumer.consumer_dlq_queue_name}.group_id"
)
async def payment_new_dlq_handler(message: Dict[str, Any]) -> None:
    """Обработка события в очереди DLQ `payments.new.dlq`"""
    message_id = message.get("payment_id", "-")
    retry_count = message.get("x-retry-count", "?")
    logger.warning(
        f"Message in DLQ, payment_id={message_id}, total_attempts={retry_count}. Message payload: {repr(message)}"
    )
    # TODO: Integrate with monitoring/alerting (e.g., send to Sentry, alert Slack)


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
