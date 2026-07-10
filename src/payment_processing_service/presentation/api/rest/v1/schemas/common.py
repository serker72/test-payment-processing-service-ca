from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentMetaDataSchema(BaseModel):
    """Схема метаданных платежа"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    address: str = Field(description="Номер карты/кошелька")
    fio: str = Field(default=None, description="ФИО владельца карты/кошелька")
    exp_date: str | None = Field(default=None, description="Срок действия карты")
    bank: str | None = Field(default=None, description="Наименование банка")
    phone: str | None = Field(default=None, description="Номер телефона")


class PaymentBaseSchema(BaseModel):
    """Схема общих данных платежа"""

    amount: Decimal = Field(description="Сумма")
    currency: str = Field(description="Валюта")
    description: str = Field(description="Описание")
    meta_data: PaymentMetaDataSchema = Field(description="Метаданные")
    webhook_url: str | None = Field(default=None, description="URL для уведомления о результате")
    expired_at: datetime | None = Field(default=None, description="Срок действия")
    status: str | None = Field(default=None, description="Статус")
    idempotency_key: str | None = Field(default=None, description="Уникальный ключ для защиты от дублей")
