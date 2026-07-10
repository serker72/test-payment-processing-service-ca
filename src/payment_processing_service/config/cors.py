from typing import final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class CORSSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: list[str] = Field(["http://localhost:3000", "http://localhost:8080"])
    cors_allow_credentials: bool = Field(True)
    cors_allow_methods: list[str] = Field(["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: list[str] = Field(["*"])
