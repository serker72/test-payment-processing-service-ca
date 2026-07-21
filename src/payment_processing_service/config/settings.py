from pydantic import Field
from pydantic_settings import BaseSettings

from payment_processing_service.config.app import AppSettings
from payment_processing_service.config.circuit_breaker import CircuitBreakerSettings
from payment_processing_service.config.consumer import ConsumerSettings
from payment_processing_service.config.cors import CORSSettings
from payment_processing_service.config.database import DatabaseSettings
from payment_processing_service.config.kafka_broker import KafkaBrokerSettings
from payment_processing_service.config.opentelemetry import OpenTelemetrySettings
from payment_processing_service.config.rabbit_broker import RabbitBrokerSettings
from payment_processing_service.config.redis import RedisSettings
from payment_processing_service.config.sqlalchemy import SQLAlchemySettings


class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    rabbit_broker: RabbitBrokerSettings = Field(default_factory=RabbitBrokerSettings)
    kafka_broker: KafkaBrokerSettings = Field(default_factory=KafkaBrokerSettings)
    consumer: ConsumerSettings = Field(default_factory=ConsumerSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    circuit_breaker: CircuitBreakerSettings = Field(default_factory=CircuitBreakerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    open_telemetry: OpenTelemetrySettings = Field(default_factory=OpenTelemetrySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    sqlalchemy: SQLAlchemySettings = Field(default_factory=SQLAlchemySettings)

    @property
    def database_url(self) -> str:
        """Получение URL подключения к серверу PostgreSQL"""
        return str(self.database.database_url)

    @property
    def test_database_url(self) -> str:
        """Получение URL подключения к серверу PostgreSQL, БД test"""
        return str(self.database.test_database_url)

    @property
    def redis_url(self) -> str:
        """Получение URL подключения к серверу Redis"""
        return str(self.redis.redis_url)

    @property
    def rabbit_broker_url(self) -> str:
        """Получение URL подключения к серверу RabbitMQ"""
        return str(self.rabbit_broker.broker_url)

    @property
    def kafka_broker_url(self) -> str:
        """Получение URL подключения к серверу Kafka"""
        return str(self.kafka_broker.broker_url)
