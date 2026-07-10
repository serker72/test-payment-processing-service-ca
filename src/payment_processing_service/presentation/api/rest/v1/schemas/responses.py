from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from payment_processing_service.presentation.api.rest.v1.schemas.common import PaymentBaseSchema


class PaymentResponseSchema(PaymentBaseSchema):
    """Схема данных платежа"""

    model_config = ConfigDict(frozen=True, extra="forbid", from_attributes=True)

    id: UUID = Field(description="ID платежа")
    created_at: datetime = Field(description="Время создания")
    updated_at: datetime | None = Field(default=None, description="Время изменения")
    processing_error_message: str | None = Field(default=None, description="Сообщение об ошибке обработки")


class PaymentCreateResponseSchema(BaseModel):
    """Схема ответа на запрос создания платежа"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    payment_id: str = Field(description="ID платежа")
    status: str = Field(description="Статус")
    created_at: datetime = Field(description="Время создания")
