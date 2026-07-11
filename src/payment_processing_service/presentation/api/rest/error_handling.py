from circuit_breaker.exceptions import CircuitBreakerRemoteCallException
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from idemptx.exceptions import IdempotencyConflictException, IdempotencyException

from payment_processing_service.application.exceptions import (
    FailedPublishPaymentMessageBrokerException,
    PaymentNotFoundError,
)
from payment_processing_service.domain.exceptions import (
    DomainValidationError,
    InvalidCurrencyException,
    InvalidPaymentStatusException,
    InvalidValueException,
)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CircuitBreakerRemoteCallException)
    async def circuit_breaker_remote_call_exception_handler(
        request: Request, exc: CircuitBreakerRemoteCallException
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"message": str(exc)})

    @app.exception_handler(PaymentNotFoundError)
    async def payment_not_found_exception_handler(request: Request, exc: PaymentNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(exc)})

    @app.exception_handler(InvalidValueException)
    async def invalid_value_exception_handler(request: Request, exc: InvalidValueException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"message": str(exc)})

    @app.exception_handler(FailedPublishPaymentMessageBrokerException)
    async def failed_publish_payment_message_broker_exception_handler(
        request: Request, exc: FailedPublishPaymentMessageBrokerException
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})

    @app.exception_handler(DomainValidationError)
    async def domain_validation_exception_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"message": str(exc)})

    @app.exception_handler(InvalidCurrencyException)
    async def invalid_currency_exception_handler(request: Request, exc: InvalidCurrencyException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"message": str(exc)})

    @app.exception_handler(InvalidPaymentStatusException)
    async def invalid_payment_status_exception_handler(
        request: Request, exc: InvalidPaymentStatusException
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"message": str(exc)})

    @app.exception_handler(IdempotencyConflictException)
    async def idempotency_conflict_exception_handler(
        request: Request, exc: IdempotencyConflictException
    ) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"message": str(exc)})

    @app.exception_handler(IdempotencyException)
    async def idempotency_exception_handler(request: Request, exc: IdempotencyException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"message": str(exc)})
