from pydantic import ConfigDict

from payment_processing_service.presentation.api.rest.v1.schemas.common import PaymentBaseSchema


class PaymentCreateRequestSchema(PaymentBaseSchema):
    """Схема запроса создания платежа"""

    # model_config = ConfigDict(frozen=True, extra="forbid")
    model_config = ConfigDict(extra="forbid")
