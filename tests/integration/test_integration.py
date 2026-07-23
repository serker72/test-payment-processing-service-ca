"""Интеграционные тесты с PostgreSQL, RabbitMQ и Kafka."""

import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.domain.entities.payment import PaymentEntity, PaymentMetaData
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus
from payment_processing_service.infrastructures.db.models.payment import mapper_registry

# ---------------------------------------------------------------------------
# Фикстуры для PostgreSQL (через environment variables)
# ---------------------------------------------------------------------------


@pytest.fixture
def postgresql_connection():
    """Возвращает строку подключения к PostgreSQL из environment variables."""
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "test")
    password = os.getenv("POSTGRES_PASSWORD", "test")
    dbname = os.getenv("POSTGRES_DB", "test_db")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


@pytest_asyncio.fixture
async def postgresql_engine(postgresql_connection) -> AsyncEngine:
    """Создаёт асинхронный engine для PostgreSQL."""
    engine = create_async_engine(
        postgresql_connection,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def postgresql_session(postgresql_engine: AsyncEngine):
    """Создаёт сессию и таблицы для PostgreSQL."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async with postgresql_engine.begin() as conn:
        await conn.run_sync(mapper_registry.metadata.create_all)

    session_maker = async_sessionmaker(postgresql_engine, expire_on_commit=False)
    async with session_maker() as session:
        # Очищаем таблицу payments перед каждым тестом
        await session.execute(text("DELETE FROM payments"))
        await session.commit()
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Фикстуры для RabbitMQ (через environment variables)
# ---------------------------------------------------------------------------


@pytest.fixture
def rabbitmq_connection():
    """Возвращает строку подключения к RabbitMQ из environment variables."""
    host = os.getenv("RABBITMQ_HOST", "127.0.0.1")
    port = os.getenv("RABBITMQ_PORT", "5672")
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return f"amqp://{user}:{password}@{host}:{port}/"


# ---------------------------------------------------------------------------
# Интеграционные тесты
# ---------------------------------------------------------------------------


class TestPostgreSQLIntegration:
    """Интеграционные тесты с PostgreSQL."""

    @pytest.mark.integration
    async def test_save_and_get_payment(self, postgresql_session):
        """Должен сохранить и получить платёж из PostgreSQL."""
        from payment_processing_service.infrastructures.db.mappers.payment_db_mapper import PaymentDBMapper
        from payment_processing_service.infrastructures.db.repositories.payment import PaymentRepositorySQLAlchemy

        entity = PaymentEntity(
            id=uuid4(),
            amount=Decimal("1500.00"),
            currency=Currency(value=CurrencyEnum.RUB),
            description="Test payment",
            meta_data=PaymentMetaData(
                address="1234567890123456",
                fio="Test User",
                exp_date="12/25",
                bank="Test Bank",
                phone="+79001234567",
            ),
            status=PaymentStatus(value=PaymentStatusEnum.pending),
            idempotency_key="test-idempotency-key",
            webhook_url="https://example.com/webhook",
            expired_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mapper = PaymentDBMapper()
        repository = PaymentRepositorySQLAlchemy(
            session=postgresql_session,
            mapper=mapper,
        )

        # Сохраняем
        await repository.save(entity)
        await postgresql_session.commit()

        # Получаем
        result = await repository.get_by_id(entity.id)
        assert result is not None
        assert result.id == entity.id
        assert result.amount == entity.amount
        assert result.status.value == entity.status.value

    @pytest.mark.integration
    async def test_get_by_idempotency_key(self, postgresql_session):
        """Должен найти платёж по idempotency_key."""
        from payment_processing_service.infrastructures.db.mappers.payment_db_mapper import PaymentDBMapper
        from payment_processing_service.infrastructures.db.repositories.payment import PaymentRepositorySQLAlchemy

        entity = PaymentEntity(
            id=uuid4(),
            amount=Decimal("1500.00"),
            currency=Currency(value=CurrencyEnum.USD),
            description="Test payment",
            meta_data=PaymentMetaData(
                address="1234567890123456",
                fio="Test User",
            ),
            status=PaymentStatus(value=PaymentStatusEnum.succeeded),
            idempotency_key="unique-idempotency-key",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mapper = PaymentDBMapper()
        repository = PaymentRepositorySQLAlchemy(
            session=postgresql_session,
            mapper=mapper,
        )

        await repository.save(entity)
        await postgresql_session.commit()

        result = await repository.get_by_idempotency_key("unique-idempotency-key")
        assert result is not None
        assert result.idempotency_key == "unique-idempotency-key"

    @pytest.mark.integration
    async def test_payment_not_found(self, postgresql_session):
        """Должен вернуть None, если платёж не найден."""
        from payment_processing_service.infrastructures.db.mappers.payment_db_mapper import PaymentDBMapper
        from payment_processing_service.infrastructures.db.repositories.payment import PaymentRepositorySQLAlchemy

        mapper = PaymentDBMapper()
        repository = PaymentRepositorySQLAlchemy(
            session=postgresql_session,
            mapper=mapper,
        )

        result = await repository.get_by_id(uuid4())
        assert result is None

        result = await repository.get_by_idempotency_key("non-existent-key")
        assert result is None


class TestRabbitMQIntegration:
    """Интеграционные тесты с RabbitMQ."""

    @pytest.mark.integration
    async def test_rabbitmq_connection(self, rabbitmq_connection):
        """Должен подключиться к RabbitMQ."""
        import pika

        # Парсим connection string
        conn_parts = rabbitmq_connection.replace("amqp://", "").split("@")
        credentials_part = conn_parts[0].split(":")
        host_port_part = conn_parts[1].split("/")

        user = credentials_part[0]
        password = credentials_part[1]
        host_port = host_port_part[0].split(":")
        host = host_port[0]
        port = int(host_port[1])

        credentials = pika.PlainCredentials(user, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Создаём тестовую очередь
        queue_name = "test.integration.queue"
        channel.queue_declare(queue=queue_name, durable=True)

        # Публикуем сообщение
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body="test message",
        )

        # Получаем сообщение
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)
        assert body == b"test message"

        connection.close()


# ---------------------------------------------------------------------------
# Фикстуры для Kafka (через environment variables)
# ---------------------------------------------------------------------------


@pytest.fixture
def kafka_connection():
    """Возвращает строку подключения к Kafka из environment variables."""
    host = os.getenv("KAFKA_HOST", "127.0.0.1")
    port = os.getenv("KAFKA_PORT", "9092")
    return f"{host}:{port}"


# ---------------------------------------------------------------------------
# Интеграционные тесты с Kafka
# ---------------------------------------------------------------------------


class TestKafkaIntegration:
    """Интеграционные тесты с Kafka."""

    @pytest.mark.integration
    async def test_kafka_connection(self, kafka_connection):
        """Должен подключиться к Kafka."""
        from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

        producer = AIOKafkaProducer(
            bootstrap_servers=kafka_connection,
            value_serializer=lambda v: v.encode("utf-8"),
        )

        consumer = AIOKafkaConsumer(
            "test.integration.kafka",
            bootstrap_servers=kafka_connection,
            auto_offset_reset="earliest",
            group_id="test.integration.group",
            value_deserializer=lambda m: m.decode("utf-8"),
        )

        await producer.start()
        await consumer.start()

        try:
            # Создаём тестовую тему через публикацию
            await producer.send_and_wait("test.integration.kafka", "test message")

            # Читаем сообщение
            messages = []
            async for msg in consumer:
                messages.append(msg)
                if len(messages) >= 1:
                    break

            assert len(messages) >= 1
            assert messages[0].value == "test message"
        finally:
            await producer.stop()
            await consumer.stop()

    @pytest.mark.integration
    async def test_kafka_dlq_ttl_config(self, kafka_connection):
        """Должен проверить, что DLQ тема создана с правильным TTL (retention.ms)."""
        from aiokafka.admin import AIOKafkaAdminClient

        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=kafka_connection,
        )

        await admin_client.start()

        try:
            dlq_topic_name = "payments.new.dlq"

            # Создаём DLQ тему с нужным TTL
            from aiokafka.admin import NewTopic

            new_topic = NewTopic(
                name=dlq_topic_name,
                num_partitions=1,
                replication_factor=1,
                topic_configs={"retention.ms": "604800000"},
            )

            # Создаём тему
            futures = await admin_client.create_topics([new_topic])
            try:
                for future in futures:
                    await future
            except Exception:
                # Тема может уже существовать
                pass

            # Получаем список тем
            topics = await admin_client.list_topics()

            # Проверяем, что DLQ тема существует
            assert dlq_topic_name in topics, (
                f"DLQ topic '{dlq_topic_name}' not found in Kafka. Available topics: {topics}"
            )

            # Получаем конфигурацию топика
            from aiokafka.admin.client import ConfigResource, ConfigResourceType

            config_resource = ConfigResource(ConfigResourceType.TOPIC, dlq_topic_name)
            topic_configs = await admin_client.describe_configs([config_resource])

            # Парсим конфигурацию из ответа
            retention_value = None
            for resource_response in topic_configs:
                for resource_tuple in resource_response.resources:
                    # resource_tuple = (type, _, _, name, [config_list])
                    if len(resource_tuple) >= 5 and resource_tuple[3] == dlq_topic_name:
                        config_list = resource_tuple[4]
                        for cfg in config_list:
                            # cfg = (name, value, is_default, source_type, ...)
                            if cfg[0] == "retention.ms":
                                retention_value = cfg[1]
                                break

            # Проверяем presence retention.ms в конфигурации
            assert retention_value is not None, "retention.ms not found in DLQ topic config"

            # TTL должен быть 604800000 мс (7 дней)
            expected_ttl = 604800000
            actual_ttl = int(retention_value) if retention_value else 0
            assert actual_ttl == expected_ttl, f"Expected retention.ms={expected_ttl}, got {actual_ttl}"
        finally:
            await admin_client.close()

    @pytest.mark.integration
    async def test_kafka_publish_and_consume(self, kafka_connection):
        """Должен опубликовать и прочитать сообщение из Kafka."""
        import json

        from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

        test_topic = "test.integration.kafka.publish"
        test_message = {"payment_id": "test-payment-001", "amount": 1000}

        producer = AIOKafkaProducer(
            bootstrap_servers=kafka_connection,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        consumer = AIOKafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_connection,
            auto_offset_reset="earliest",
            group_id="test.integration.consume.group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await producer.start()
        await consumer.start()

        try:
            # Публикуем
            future = producer.send(test_topic, value=test_message)
            record_metadata = await future
            assert record_metadata is not None

            # Читаем
            messages = []
            async for msg in consumer:
                messages.append(msg)
                if len(messages) >= 1:
                    break

            assert len(messages) >= 1
            assert messages[0].value["payment_id"] == "test-payment-001"
            assert messages[0].value["amount"] == 1000
        finally:
            await producer.stop()
            await consumer.stop()
