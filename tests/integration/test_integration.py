"""Интеграционные тесты с PostgreSQL и RabbitMQ."""

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
