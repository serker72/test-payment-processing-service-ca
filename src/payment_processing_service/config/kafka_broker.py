from typing import final

from pydantic import Field, KafkaDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class KafkaBrokerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    kafka_host: str = Field("localhost")
    kafka_port: int = Field(9092)

    @computed_field
    # def broker_url(self) -> KafkaDsn:
    def broker_url(self) -> str:
        """Получение URL подключения к серверу Kafka"""
        # return KafkaDsn.build(
        #     scheme="kafka",
        #     host=self.kafka_host,
        #     port=self.kafka_port,
        # )
        return f"{self.kafka_host}:{self.kafka_port}"
