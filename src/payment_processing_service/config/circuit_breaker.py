from typing import final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class CircuitBreakerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    circuit_breaker_half_open_retry_count: int = Field(3)
    circuit_breaker_half_open_retry_timeout_seconds: int = Field(30)
