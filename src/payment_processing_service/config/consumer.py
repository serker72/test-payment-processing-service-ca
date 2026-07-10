from typing import final

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class ConsumerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    consumer_exchange_name: str = Field("payments")
    consumer_payment_routing_key: str = Field("payment.created")
    consumer_queue_name: str = Field("payments.new")
    consumer_queue_delivery_limit: int = Field(3)
    consumer_dlx_exchange_name: str = Field("payments.dlx")
    consumer_dead_letter_routing_key: str = Field("dlq")
    consumer_dlq_queue_name: str = Field("payments.new.dlq")
    consumer_dlq_queue_message_ttl: int = Field(604800000)
