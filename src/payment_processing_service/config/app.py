from typing import final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_debug: bool = Field(False, description="Флаг отладки")
    backend_base_url: str = Field("http://localhost:8000", description="Основной URL")
    backend_api_prefix: str = Field("/api/v1", description="Префикс")
    backend_authentication_header_key: str = Field(description="Заголовок с ключом API")
    backend_authentication_header_value: str = Field(description="Значение ключа API")
    backend_payment_success_rate: float | int = Field(0.9)
    backend_payment_min_delay: int = Field(2)
    backend_payment_max_delay: int = Field(5)
    backend_webhook_retry_attempts: int = Field(3)
    backend_webhook_request_timeout: float | int = Field(10)
    backend_webhook_retry_delay_base: float | int = Field(1.0)
    backend_outbox_poll_interval: float | int = Field(2.0)
