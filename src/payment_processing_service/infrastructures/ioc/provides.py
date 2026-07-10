from asyncio import current_task
from collections.abc import AsyncIterator
from typing import AsyncIterable

from dishka import Provider, Scope, provide
from faststream.rabbit.fastapi import RabbitBroker
from httpx import AsyncClient
from idemptx.backend import AsyncRedisBackend
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from payment_processing_service.application.interfaces.mappers import DtoPaymentEntityMapperProtocol
from payment_processing_service.application.interfaces.message_broker import PaymentMessageBrokerPublisherProtocol
from payment_processing_service.application.interfaces.repositories import PaymentRepositoryProtocol
from payment_processing_service.application.interfaces.serialization import PaymentSerializationMapperProtocol
from payment_processing_service.application.interfaces.uow import PaymentUnitOfWorkProtocol
from payment_processing_service.application.interfaces.webhooks import SendPaymentWebhookProtocol
from payment_processing_service.application.mappers import PaymentMapper
from payment_processing_service.application.use_cases.create_payment import CreatePaymentUseCase
from payment_processing_service.application.use_cases.execute_payment import ExecutePaymentUseCase
from payment_processing_service.application.use_cases.get_payment_from_repo import (
    GetPaymentByIdempotencyKeyFromRepoUseCase,
    GetPaymentByIdFromRepoUseCase,
)
from payment_processing_service.application.use_cases.process_payment import ProcessPaymentUseCase
from payment_processing_service.application.use_cases.process_payment_webhook import ProcessPaymentWebhookUseCase
from payment_processing_service.application.use_cases.publish_payment_to_broker import PublishPaymentToBrokerUseCase
from payment_processing_service.application.use_cases.save_payment_to_repo import SavePaymentToRepoUseCase
from payment_processing_service.application.use_cases.send_payment_webhook import SendPaymentWebhookUseCase
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.broker.rabbit import RabbitPublisher
from payment_processing_service.infrastructures.db.mappers import PaymentDBMapper
from payment_processing_service.infrastructures.db.payment_uow import PaymentSQLAlchemyUnitOfWork
from payment_processing_service.infrastructures.db.repositories.payment import PaymentRepositorySQLAlchemy
from payment_processing_service.infrastructures.http.clients import SendPaymentWebhookClient
from payment_processing_service.infrastructures.mappers.payment import InfrastructurePaymentMapper
from payment_processing_service.presentation.api.rest.v1.mappers.payment_mapper import PaymentPresentationMapper


class SettingsProvider(Provider):
    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        """Предоставляет экземпляр Settings"""
        return Settings()


class HTTPClientProvider(Provider):
    """Предоставляет асинхронный HTTP-клиент."""

    @provide(scope=Scope.APP)
    async def get_http_client(self, settings: Settings) -> AsyncIterator[AsyncClient]:
        """Предоставляет экземпляр AsyncClient с настроенным тайм-аутом."""
        client = AsyncClient(timeout=settings.app.backend_webhook_request_timeout)
        try:
            yield client
        finally:
            await client.aclose()


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_broker(self, settings: Settings) -> AsyncIterator[RabbitBroker]:
        """Предоставляет экземпляр RabbitBroker."""
        broker = RabbitBroker(settings.broker_url)
        try:
            await broker.start()
            yield broker
        finally:
            await broker.stop()


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_async_engine(self, settings: Settings) -> AsyncEngine:
        """Предоставляет экземпляр AsyncEngine."""
        return create_async_engine(
            settings.database_url,
            echo=settings.sqlalchemy.sqlalchemy_debug,
            max_overflow=settings.sqlalchemy.sqlalchemy_max_overflow,
            pool_size=settings.sqlalchemy.sqlalchemy_pool_size,
            pool_timeout=settings.sqlalchemy.sqlalchemy_pool_timeout,
            pool_recycle=settings.sqlalchemy.sqlalchemy_pool_recycle,
            pool_use_lifo=settings.sqlalchemy.sqlalchemy_pool_use_lifo,
            pool_pre_ping=settings.sqlalchemy.sqlalchemy_pool_pre_ping,
        )

    @provide(scope=Scope.APP)
    def provide_async_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        """Создание фабрики для AsyncSession."""
        return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def provide_async_session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        """Предоставляет экземпляр AsyncSession."""
        async_session = async_scoped_session(session_factory=session_factory, scopefunc=current_task)
        try:
            async with async_session() as session:
                yield session
        except Exception:
            await async_session.rollback()
            raise
        finally:
            await async_session.remove()


class AsyncRedisProvider(Provider):
    @provide(scope=Scope.APP)
    def get_async_redis_client(self, settings: Settings) -> Redis:
        """Предоставляет экземпляр Redis."""
        return Redis.from_url(settings.redis_url)

    @provide(scope=Scope.APP)
    def get_async_idemptx_backend(self, async_redis_client: Redis) -> AsyncRedisBackend:
        """Предоставляет экземпляр AsyncRedisBackend."""
        return AsyncRedisBackend(async_redis_client)


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_payment_repository(self, session: AsyncSession, db_mapper: PaymentDBMapper) -> PaymentRepositoryProtocol:
        """Предоставляет реализацию PaymentRepositoryProtocol."""
        return PaymentRepositorySQLAlchemy(session=session, mapper=db_mapper)


class UnitOfWorkProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_unit_of_work(
        self,
        session: AsyncSession,
        repository: PaymentRepositoryProtocol,
    ) -> PaymentUnitOfWorkProtocol:
        """Предоставляет реализацию PaymentUnitOfWorkProtocol."""
        return PaymentSQLAlchemyUnitOfWork(session=session, repository=repository)


class ServiceProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_send_payment_webhook_client(
        self,
        client: AsyncClient,
        infrastructure_mapper: PaymentSerializationMapperProtocol,
    ) -> SendPaymentWebhookProtocol:
        """Предоставляет реализацию SendPaymentWebhookProtocol."""
        return SendPaymentWebhookClient(
            client=client,
            mapper=infrastructure_mapper,
        )

    @provide(scope=Scope.REQUEST)
    def get_message_broker(
        self,
        settings: Settings,
        broker: RabbitBroker,
        infrastructure_mapper: PaymentSerializationMapperProtocol,
    ) -> PaymentMessageBrokerPublisherProtocol:
        """Предоставляет реализацию MessageBrokerPublisherProtocol."""
        return RabbitPublisher(
            settings=settings,
            broker=broker,
            mapper=infrastructure_mapper,
        )


class MapperProvider(Provider):
    """Предоставляет различные реализации мапперов для разных слоёв."""

    @provide(scope=Scope.APP)
    def get_payment_mapper(self) -> DtoPaymentEntityMapperProtocol:
        """Предоставляет маппер слоя приложения (Domain Entity <-> Application DTO)."""
        return PaymentMapper()

    @provide(scope=Scope.REQUEST)
    def get_db_mapper(self) -> PaymentDBMapper:
        """Предоставляет маппер базы данных (Доменная сущность <-> модель SQLAlchemy)."""
        return PaymentDBMapper()

    @provide(scope=Scope.REQUEST)
    def get_infrastructure_payment_mapper(self) -> PaymentSerializationMapperProtocol:
        """Предоставляет маппер слоя инфраструктуры (Application DTO <-> Pydantic/JSON)."""
        return InfrastructurePaymentMapper()

    @provide(scope=Scope.REQUEST)
    def get_presentation_payment_mapper(self) -> PaymentPresentationMapper:
        """Предоставляет маппер слоя представления (Application DTO -> Response Schema)."""
        return PaymentPresentationMapper()


class UseCaseProvider(Provider):
    """Предоставляет сценарии применения приложений."""

    @provide(scope=Scope.REQUEST)
    def get_get_payment_by_id_from_repo_use_case(
        self, uow: PaymentUnitOfWorkProtocol, payment_mapper: DtoPaymentEntityMapperProtocol
    ) -> GetPaymentByIdFromRepoUseCase:
        """Предоставляет экземпляр GetPaymentByIdFromRepoUseCase."""
        return GetPaymentByIdFromRepoUseCase(uow=uow, payment_mapper=payment_mapper)

    @provide(scope=Scope.REQUEST)
    def get_get_payment_by_idempotency_ke_from_repo_use_case(
        self, uow: PaymentUnitOfWorkProtocol, payment_mapper: DtoPaymentEntityMapperProtocol
    ) -> GetPaymentByIdempotencyKeyFromRepoUseCase:
        """Предоставляет экземпляр GetPaymentByIdempotencyKeyFromRepoUseCase."""
        return GetPaymentByIdempotencyKeyFromRepoUseCase(uow=uow, payment_mapper=payment_mapper)

    @provide(scope=Scope.REQUEST)
    def get_save_payment_to_repo_use_case(
        self, uow: PaymentUnitOfWorkProtocol, payment_mapper: DtoPaymentEntityMapperProtocol
    ) -> SavePaymentToRepoUseCase:
        """Предоставляет экземпляр SavePaymentToRepoUseCase."""
        return SavePaymentToRepoUseCase(uow=uow, payment_mapper=payment_mapper)

    @provide(scope=Scope.REQUEST)
    def get_publish_payment_to_broker_use_case(
        self,
        message_broker: PaymentMessageBrokerPublisherProtocol,
        payment_mapper: DtoPaymentEntityMapperProtocol,
    ) -> PublishPaymentToBrokerUseCase:
        """Предоставляет экземпляр PublishPaymentToBrokerUseCase."""
        return PublishPaymentToBrokerUseCase(message_broker=message_broker, payment_mapper=payment_mapper)

    @provide(scope=Scope.REQUEST)
    def get_create_payment_use_case(
        self,
        get_payment_by_id_from_repo_use_case: GetPaymentByIdFromRepoUseCase,
        get_payment_by_idempotency_key_from_repo_use_case: GetPaymentByIdempotencyKeyFromRepoUseCase,
        save_payment_to_repo_use_case: SavePaymentToRepoUseCase,
        publish_payment_to_broker_use_case: PublishPaymentToBrokerUseCase,
    ) -> CreatePaymentUseCase:
        """Предоставляет экземпляр CreatePaymentUseCase."""
        return CreatePaymentUseCase(
            get_payment_by_id_from_repo_use_case=get_payment_by_id_from_repo_use_case,
            get_payment_by_idempotency_key_from_repo_use_case=get_payment_by_idempotency_key_from_repo_use_case,
            save_payment_to_repo_use_case=save_payment_to_repo_use_case,
            publish_payment_to_broker_use_case=publish_payment_to_broker_use_case,
        )

    @provide(scope=Scope.REQUEST)
    def get_execute_payment_use_case(self, settings: Settings) -> ExecutePaymentUseCase:
        """Предоставляет экземпляр ExecutePaymentUseCase."""
        return ExecutePaymentUseCase(settings=settings)

    @provide(scope=Scope.REQUEST)
    def get_send_payment_webhook_use_case(
        self,
        http_client: SendPaymentWebhookProtocol,
        payment_mapper: DtoPaymentEntityMapperProtocol,
    ) -> SendPaymentWebhookUseCase:
        """Предоставляет экземпляр SendPaymentWebhookUseCase."""
        return SendPaymentWebhookUseCase(http_client=http_client, payment_mapper=payment_mapper)

    @provide(scope=Scope.REQUEST)
    def get_process_payment_webhook_use_case(self, settings: Settings) -> ProcessPaymentWebhookUseCase:
        """Предоставляет экземпляр ProcessPaymentWebhookUseCase."""
        return ProcessPaymentWebhookUseCase(settings=settings)

    @provide(scope=Scope.REQUEST)
    def get_process_payment_use_case(
        self,
        uow: PaymentUnitOfWorkProtocol,
        get_payment_by_id_from_repo_use_case: GetPaymentByIdFromRepoUseCase,
        execute_payment_use_case: ExecutePaymentUseCase,
        save_payment_to_repo_use_case: SavePaymentToRepoUseCase,
        send_payment_webhook_use_case: SendPaymentWebhookUseCase,
    ) -> ProcessPaymentUseCase:
        """Предоставляет экземпляр ProcessPaymentUseCase."""
        return ProcessPaymentUseCase(
            uow=uow,
            get_payment_by_id_from_repo_use_case=get_payment_by_id_from_repo_use_case,
            execute_payment_use_case=execute_payment_use_case,
            save_payment_to_repo_use_case=save_payment_to_repo_use_case,
            send_payment_webhook_use_case=send_payment_webhook_use_case,
        )
