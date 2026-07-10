from typing import final

from pydantic import Field, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    redis_username: str = Field("default")
    redis_password: str = Field("")
    redis_host: str = Field("localhost")
    redis_port: int = Field(6379)
    redis_db: int = Field(0)

    @computed_field
    def redis_url(self) -> RedisDsn:
        """Получение URL подключения к серверу Redis"""
        return RedisDsn.build(
            scheme="redis",
            username=self.redis_username if self.redis_username != "default" else None,
            password=self.redis_password if self.redis_password else None,
            host=self.redis_host,
            port=self.redis_port,
            path=str(self.redis_db),
        )
