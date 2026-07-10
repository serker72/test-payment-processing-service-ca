from typing import final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class SQLAlchemySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sqlalchemy_debug: bool = Field(False)
    sqlalchemy_pool_size: int = Field(50)
    sqlalchemy_max_overflow: int = Field(-1)
    sqlalchemy_pool_timeout: float | int = Field(30.0)
    sqlalchemy_pool_recycle: int = Field(600)
    sqlalchemy_pool_use_lifo: bool = Field(False)
    sqlalchemy_pool_pre_ping: bool = Field(True)
