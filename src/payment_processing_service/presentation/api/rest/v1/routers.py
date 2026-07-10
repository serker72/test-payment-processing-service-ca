from fastapi import APIRouter

from payment_processing_service.presentation.api.rest.v1.controllers.health_check_controller import (
    router as health_check_router,
)
from payment_processing_service.presentation.api.rest.v1.controllers.payment_controller import router as payment_router
from payment_processing_service.presentation.api.rest.v1.controllers.webhook_controller import router as webhook_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_check_router)
api_v1_router.include_router(webhook_router)
api_v1_router.include_router(payment_router)
