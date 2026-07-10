import sys

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from payment_processing_service.config import constants as c
from payment_processing_service.config.settings import Settings
from payment_processing_service.infrastructures.external.opentelemetry import initialize_telemetry
from payment_processing_service.infrastructures.ioc.di import get_providers
from payment_processing_service.presentation.api.rest.error_handling import setup_exception_handlers
from payment_processing_service.presentation.api.rest.middlewares.api_key_header import ApiKeyHeaderMiddleware
from payment_processing_service.presentation.api.rest.middlewares.request_processing_time import (
    RequestProcessingTimeMiddleware,
)
from payment_processing_service.presentation.api.rest.v1.routers import api_v1_router
from payment_processing_service.presentation.utils.helpers.custom_json import CustomJSONResponse
from payment_processing_service.presentation.utils.helpers.project import get_project_info

without_authentication_endpoints = ["/", "/docs", "/redoc", "/openapi.json", "/api/v1/healthcheck", "/api/v1/webhooks"]

container: AsyncContainer = make_async_container(*(get_providers() + [FastapiProvider()]))

settings = container.get_sync(Settings)

log_level = "DEBUG" if settings.app.backend_debug is True else "INFO"
logger.remove()
logger.add(sys.stderr, format=c.FORMAT_LOG_APP, level=log_level)
log_extra = {"request_id": "-", "user_ip": "-"}
logger.configure(extra=log_extra)

project_info = get_project_info()

initialize_telemetry(project_info, settings.open_telemetry.collector_host, settings.open_telemetry.collector_port)
app = FastAPI(
    title=project_info["description"], version=project_info["version"], default_response_class=CustomJSONResponse
)

app.add_middleware(RequestProcessingTimeMiddleware)
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.cors.cors_origins,
    allow_credentials=settings.cors.cors_allow_credentials,
    allow_methods=settings.cors.cors_allow_methods,
    allow_headers=settings.cors.cors_allow_headers,
)
app.add_middleware(
    ApiKeyHeaderMiddleware,  # type: ignore[arg-type]
    key_value=settings.app.backend_authentication_header_value,
    header_name=settings.app.backend_authentication_header_key,
    ignored_endpoints=without_authentication_endpoints,
)


FastAPIInstrumentor.instrument_app(app)

setup_dishka(container, app)

setup_exception_handlers(app)
app.include_router(api_v1_router, prefix="/api")
