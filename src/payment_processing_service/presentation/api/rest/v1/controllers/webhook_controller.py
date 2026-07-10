from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from payment_processing_service.application.use_cases.process_payment_webhook import ProcessPaymentWebhookUseCase
from payment_processing_service.presentation.utils.helpers import custom_json

router = APIRouter(prefix="/v1/webhooks", tags=["Webhooks"], route_class=DishkaRoute)


@router.post("", response_model=dict)
async def processing(
    data: dict,
    use_case: FromDishka[ProcessPaymentWebhookUseCase] = None,
):
    """Обработка вебхука"""
    response_data = await use_case(data)
    return custom_json.CustomJSONResponse(
        content=response_data,
        status_code=status.HTTP_200_OK if response_data.get("status") == "success" else status.HTTP_400_BAD_REQUEST,
    )
