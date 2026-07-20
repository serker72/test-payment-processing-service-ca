from typing import final

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = Field("localhost")
    postgres_port: int = Field(5432)
    postgres_db: str = Field("payment_processing")
    postgres_user: str = Field("payment_processing")
    postgres_password: str = Field("payment_processing")
    postgres_test_db: str = Field("payment_processing_test")
    postgres_test_user: str = Field("payment_processing_test")
    postgres_test_password: str = Field("payment_processing_test")

    @computed_field
    def database_url(self) -> PostgresDsn:
        """Получение URL подключения к серверу PostgreSQL"""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )

    @computed_field
    def test_database_url(self) -> PostgresDsn:
        """Получение URL подключения к серверу PostgreSQL, БД test"""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_test_user,
            password=self.postgres_test_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_test_db,
        )
