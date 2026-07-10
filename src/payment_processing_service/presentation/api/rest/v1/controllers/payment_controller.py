from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Body, Path, Request, status
from idemptx import idempotent
from idemptx.backend import AsyncRedisBackend

from payment_processing_service.application.use_cases.create_payment import CreatePaymentUseCase
from payment_processing_service.application.use_cases.get_payment_from_repo import GetPaymentByIdFromRepoUseCase
from payment_processing_service.config.enums import PaymentStatusEnum
from payment_processing_service.presentation.api.rest.v1.mappers.payment_mapper import PaymentPresentationMapper
from payment_processing_service.presentation.api.rest.v1.schemas import (
    PaymentCreateRequestSchema,
    PaymentCreateResponseSchema,
    PaymentResponseSchema,
)
from payment_processing_service.presentation.utils.helpers import custom_json

router = APIRouter(prefix="/v1/payments", tags=["Payments"], route_class=DishkaRoute)


@router.get(
    "/{entity_id}",
    response_model=PaymentResponseSchema,
    summary="Get payment by ID",
    responses={
        200: {"description": "Payment retrieved successfully"},
        404: {"description": "Payment not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_payment(
    entity_id: UUID = Path(description="Payment UUID"),
    use_case: FromDishka[GetPaymentByIdFromRepoUseCase] = None,
    presentation_mapper: FromDishka[PaymentPresentationMapper] = None,
) -> PaymentResponseSchema:
    """Получение данных платежа"""
    payment_dto = await use_case(str(entity_id))
    return presentation_mapper.to_response(payment_dto)


@router.post(
    "",
    response_model=PaymentCreateResponseSchema,
    summary="Create new payment",
    responses={
        200: {"description": "Payment created successfully"},
        500: {"description": "Internal server error"},
    },
)
async def create_payment(
    data: Annotated[PaymentCreateRequestSchema, Body()],
    request: Request,
    async_idemptx_backend: FromDishka[AsyncRedisBackend],
    use_case: FromDishka[CreatePaymentUseCase] = None,
    presentation_mapper: FromDishka[PaymentPresentationMapper] = None,
):
    """Создание нового платежа"""

    @idempotent(storage_backend=async_idemptx_backend)
    async def create_payment_process(request: Request):
        """Создание нового платежа"""
        data.status = PaymentStatusEnum.pending.name
        data.idempotency_key = request.state.idempotency_key
        payment_dto = await use_case(presentation_mapper.from_request(data))
        result = presentation_mapper.to_create_response(payment_dto)
        return custom_json.CustomJSONResponse(content=result.model_dump(), status_code=status.HTTP_202_ACCEPTED)

    return await create_payment_process(request=request)
