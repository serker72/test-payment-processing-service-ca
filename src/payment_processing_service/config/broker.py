from typing import final

from pydantic import AmqpDsn, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class BrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rabbitmq_username: str = Field("guest")
    rabbitmq_password: str = Field("guest")
    rabbitmq_host: str = Field("localhost")
    rabbitmq_port: int = Field(5672)
    rabbitmq_vhost: str = Field("/")

    @computed_field
    def broker_url(self) -> AmqpDsn:
        """Получение URL подключения к серверу RabbitMQ"""
        return AmqpDsn.build(
            scheme="amqp",
            username=self.rabbitmq_username,
            password=self.rabbitmq_password,
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            path=self.rabbitmq_vhost,
        )
