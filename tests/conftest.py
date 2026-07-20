"""Глобальные фикстуры для тестов."""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from faker import Faker as _Faker
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.fields import Use
from sqlalchemy import NullPool, event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum

faker = _Faker()


@pytest.fixture(scope="session")
def anyio_backend():
    """Бэкенд для pytest-asyncio."""
    return "asyncio"


# ---------------------------------------------------------------------------
# SQLite In-Memory Engine
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _enable_fk(engine: AsyncEngine) -> None:
    """Включаем FOREIGN KEY в SQLite."""

    @event.listens_for(engine, "connect")
    def _set_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Создаёт асинхронный engine на SQLite in-memory для тестов."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    _enable_fk(engine)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Создаёт сессию и таблицы для каждого теста."""
    from payment_processing_service.infrastructures.db.models.payment import PaymentModel

    async with test_engine.begin() as conn:
        await conn.run_sync(PaymentModel.metadata.create_all)

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def db_session(test_session: AsyncSession) -> AsyncSession:
    """Псевдоним для test_session."""
    return test_session


# ---------------------------------------------------------------------------
# Фабрики данных (polyfactory + faker)
# ---------------------------------------------------------------------------

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentCreateNotificationDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.domain.entities.payment import (
    PaymentEntity,
    PaymentMetaData,
)
from payment_processing_service.domain.value_objects.currency import Currency
from payment_processing_service.domain.value_objects.payment_status import PaymentStatus


class PaymentEntityFactory(DataclassFactory[PaymentEntity]):
    """Фабрика для создания PaymentEntity."""

    __model__ = PaymentEntity

    amount: Decimal = Use(lambda: Decimal("1000.00"))
    currency: Currency = Use(lambda: Currency(value=CurrencyEnum.RUB))
    description: str = Use(lambda: faker.sentence(nb_words=4))
    meta_data: PaymentMetaData = Use(
        lambda: PaymentMetaData(
            address=faker.credit_card_number(),
            fio=faker.name(),
            exp_date=faker.credit_card_expire(),
            bank=faker.company(),
            phone=faker.phone_number(),
        )
    )
    status: PaymentStatus = Use(lambda: PaymentStatus(value=PaymentStatusEnum.pending))
    idempotency_key: str = Use(lambda: str(faker.uuid4()))
    webhook_url: str | None = Use(lambda: faker.uri())
    expired_at: datetime = Use(lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    processing_error_message: str | None = None
    created_at: datetime = Use(lambda: datetime.now(timezone.utc))
    updated_at: datetime = Use(lambda: datetime.now(timezone.utc))


class PaymentDTOPartialFactory(DataclassFactory[PaymentDTO]):
    """Фабрика для создания PaymentDTO."""

    __model__ = PaymentDTO

    amount: Decimal = Use(lambda: Decimal("1000.00"))
    currency: CurrencyDTO = Use(lambda: CurrencyDTO(value=CurrencyEnum.RUB))
    description: str = Use(lambda: faker.sentence(nb_words=4))
    meta_data: PaymentMetaDataDTO = Use(
        lambda: PaymentMetaDataDTO(
            address=faker.credit_card_number(),
            fio=faker.name(),
        )
    )
    status: PaymentStatusDTO = Use(lambda: PaymentStatusDTO(value=PaymentStatusEnum.pending))
    idempotency_key: str = Use(lambda: str(faker.uuid4()))
    created_at: datetime = Use(lambda: datetime.now(timezone.utc))
    updated_at: datetime = Use(lambda: datetime.now(timezone.utc))


class PaymentCreateNotificationDTOPartialFactory(DataclassFactory[PaymentCreateNotificationDTO]):
    """Фабрика для создания PaymentCreateNotificationDTO."""

    __model__ = PaymentCreateNotificationDTO

    status: PaymentStatusDTO = Use(lambda: PaymentStatusDTO(value=PaymentStatusEnum.pending))
    created_at: datetime = Use(lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Mock-объекты для протоколов (use case layer)
# ---------------------------------------------------------------------------


class MockRepository:
    """Mock репозитория для тестирования use cases."""

    def __init__(self):
        self._store: dict[str, PaymentEntity] = {}

    async def get_by_filters(self, filters):
        return None

    async def get_by_id(self, entity_id: str | UUID) -> PaymentEntity | None:
        return self._store.get(str(entity_id))

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentEntity | None:
        for entity in self._store.values():
            if entity.idempotency_key == idempotency_key:
                return entity
        return None

    async def save(self, entity: PaymentEntity) -> None:
        self._store[str(entity.id)] = entity


class MockUnitOfWork:
    """Mock Unit of Work для тестирования use cases."""

    def __init__(self, repository: MockRepository | None = None):
        self.repository = repository or MockRepository()
        self.commits = 0
        self.rollbacks = 0
        self.entered = False

    async def __aenter__(self) -> "MockUnitOfWork":
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class MockMessageBroker:
    """Mock брокера сообщений."""

    def __init__(self):
        self.published: list = []

    async def publish_new_payment(self, notification_dto) -> None:
        self.published.append(notification_dto)


class MockWebhookClient:
    """Mock HTTP-клиента для отправки вебхуков."""

    def __init__(self, should_fail: bool = False, raise_exception: Exception | None = None):
        self.should_fail = should_fail
        self.raise_exception = raise_exception
        self.sent_webhooks: list = []

    async def send_webhook(self, dto) -> None:
        self.sent_webhooks.append(dto)
        if self.should_fail:
            if self.raise_exception:
                raise self.raise_exception
            from payment_processing_service.domain.exceptions import WebhookDeliveryError

            raise WebhookDeliveryError("Webhook delivery failed")
