"""
Интеграционные тесты API с использованием FastAPI TestClient и Dishka Mock Provider.

Используем подход из документации Dishka:
https://dishka.readthedocs.io/en/stable/advanced/testing/index.html
"""

import os
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import allure
import pytest
from dishka import Provider, Scope, make_async_container, provide
from fastapi.testclient import TestClient
from idemptx.backend import AsyncRedisBackend

from payment_processing_service.application.dtos.payment import (
    CurrencyDTO,
    PaymentDTO,
    PaymentMetaDataDTO,
    PaymentStatusDTO,
)
from payment_processing_service.application.use_cases.create_payment import CreatePaymentUseCase
from payment_processing_service.application.use_cases.get_payment_from_repo import GetPaymentByIdFromRepoUseCase
from payment_processing_service.application.use_cases.process_payment_webhook import ProcessPaymentWebhookUseCase
from payment_processing_service.config.enums import CurrencyEnum, PaymentStatusEnum
from payment_processing_service.presentation.api.rest.v1.controllers.health_check_controller import (
    router as health_check_router,
)
from payment_processing_service.presentation.api.rest.v1.controllers.payment_controller import (
    router as payment_router,
)
from payment_processing_service.presentation.api.rest.v1.controllers.webhook_controller import (
    router as webhook_router,
)
from payment_processing_service.presentation.api.rest.v1.mappers.payment_mapper import (
    PaymentPresentationMapper,
)

# ---------------------------------------------------------------------------
# AllureTestClient
# ---------------------------------------------------------------------------


class AllureTestClient(TestClient):
    """TestClient с поддержкой Allure steps для HTTP-методов."""

    @allure.step("Отправка GET запроса на '{url}'")
    def get(self, url, **kwargs):
        return super().get(url, **kwargs)

    @allure.step("Отправка POST запроса на '{url}'")
    def post(self, url, **kwargs):
        return super().post(url, **kwargs)


# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

API_KEY = os.getenv(
    "BACKEND_AUTHENTICATION_HEADER_VALUE",
    "9c26c74b1b9bda81127eebd1e9f138073b2b029c877a29940724ed9784a1d92",
)
API_KEY_HEADER = os.getenv("BACKEND_AUTHENTICATION_HEADER_KEY", "x-api-key")

VALID_PAYMENT_PAYLOAD = {
    "amount": "1500.00",
    "currency": "RUB",
    "description": "Test payment",
    "meta_data": {
        "address": "1234567890123456",
        "fio": "Test User",
    },
}


# Генератор уникальных idempotency key для каждого запроса
def get_unique_idempotency_key():
    return f"idempotency-{uuid4()}"


# ---------------------------------------------------------------------------
# Mock Provider для Dishka
# ---------------------------------------------------------------------------


class MockUseCaseProvider(Provider):
    """Provider с мокированными use case для тестирования API."""

    def __init__(self, get_payment_mock, create_payment_mock, process_webhook_mock, redis_backend_mock):
        super().__init__()
        self._get_payment_mock = get_payment_mock
        self._create_payment_mock = create_payment_mock
        self._process_webhook_mock = process_webhook_mock
        self._redis_backend_mock = redis_backend_mock

    @provide(scope=Scope.REQUEST)
    def get_get_payment_use_case(self) -> GetPaymentByIdFromRepoUseCase:
        """Предоставляет мокированный use case для получения платежа."""
        return self._get_payment_mock

    @provide(scope=Scope.REQUEST)
    def get_create_payment_use_case(self) -> CreatePaymentUseCase:
        """Предоставляет мокированный use case для создания платежа."""
        return self._create_payment_mock

    @provide(scope=Scope.REQUEST)
    def get_process_webhook_use_case(self) -> ProcessPaymentWebhookUseCase:
        """Предоставляет мокированный use case для обработки вебхука."""
        return self._process_webhook_mock

    @provide(scope=Scope.REQUEST)
    def get_presentation_mapper(self) -> PaymentPresentationMapper:
        """Предоставляет маппер для преобразования DTO в response schema."""
        return PaymentPresentationMapper()

    @provide(scope=Scope.REQUEST)
    def get_async_idemptx_backend(self) -> AsyncRedisBackend:
        """Предоставляет мокированный backend для idempotency."""
        return self._redis_backend_mock


# ---------------------------------------------------------------------------
# Фикстуры моков
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_get_payment_use_case():
    """Создаёт мокированный use case для получения платежа."""
    mock = AsyncMock(spec=GetPaymentByIdFromRepoUseCase)

    def _create_payment_dto(payment_id=None, **kwargs):
        if payment_id is None:
            payment_id = uuid4()
        return PaymentDTO(
            id=payment_id,
            amount=kwargs.get("amount", Decimal("1500.00")),
            currency=CurrencyDTO(value=kwargs.get("currency", CurrencyEnum.RUB)),
            description=kwargs.get("description", "Test payment"),
            meta_data=PaymentMetaDataDTO(
                address=kwargs.get("address", "1234567890123456"),
                fio=kwargs.get("fio", "Test User"),
            ),
            status=PaymentStatusDTO(value=kwargs.get("status", PaymentStatusEnum.pending)),
            idempotency_key=kwargs.get("idempotency_key", "test-key"),
            created_at=kwargs.get("created_at", datetime.now(UTC)),
        )

    mock.return_value = _create_payment_dto()
    return mock


@pytest.fixture
def mock_async_redis_backend():
    """Создаёт мокированный AsyncRedisBackend для тестирования."""
    mock = AsyncMock(spec=AsyncRedisBackend)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_create_payment_use_case():
    """Создаёт мокированный use case для создания платежа."""
    mock = AsyncMock(spec=CreatePaymentUseCase)

    def _create_payment_dto(**kwargs):
        payment_id = kwargs.get("payment_id", uuid4())
        return PaymentDTO(
            id=payment_id,
            amount=Decimal("1500.00"),
            currency=CurrencyDTO(value=kwargs.get("currency", CurrencyEnum.RUB)),
            description=kwargs.get("description", "Test payment"),
            meta_data=PaymentMetaDataDTO(
                address=kwargs.get("address", "1234567890123456"),
                fio=kwargs.get("fio", "Test User"),
            ),
            status=PaymentStatusDTO(value=kwargs.get("status", PaymentStatusEnum.pending)),
            idempotency_key=kwargs.get("idempotency_key", "test-key"),
            created_at=kwargs.get("created_at", datetime.now(UTC)),
        )

    mock.return_value = _create_payment_dto()
    return mock


@pytest.fixture
def mock_process_webhook_use_case():
    """Создаёт мокированный use case для обработки вебхука."""
    mock = AsyncMock(spec=ProcessPaymentWebhookUseCase)
    mock.return_value = {"status": "success", "payment_id": str(uuid4())}
    return mock


# ---------------------------------------------------------------------------
# Фикстуры контейнеров
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_container(
    mock_get_payment_use_case,
    mock_create_payment_use_case,
    mock_process_webhook_use_case,
    mock_async_redis_backend,
):
    """Создаёт Dishka контейнер с мокированными use case."""
    mock_provider = MockUseCaseProvider(
        get_payment_mock=mock_get_payment_use_case,
        create_payment_mock=mock_create_payment_use_case,
        process_webhook_mock=mock_process_webhook_use_case,
        redis_backend_mock=mock_async_redis_backend,
    )
    test_container = make_async_container(mock_provider)
    yield test_container


# ---------------------------------------------------------------------------
# Фикстуры тестового приложения
# ---------------------------------------------------------------------------


@pytest.fixture
def test_app():
    """Создаёт тестовое FastAPI приложение с middleware и роутерами."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    app = FastAPI(title="Test API", version="0.1.0")

    class ApiKeyHeaderMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, key_value, header_name="X-Api-Key", ignored_endpoints=None):
            super().__init__(app)
            self.header_name = header_name
            self.key_value = key_value
            self.ignored_endpoints = ignored_endpoints or []

        async def dispatch(self, request: Request, call_next):
            if request.url.path in self.ignored_endpoints:
                return await call_next(request)

            header_value = request.headers.get(self.header_name)
            if not header_value or header_value != self.key_value:
                return JSONResponse(
                    content=f"API key {'not found' if not header_value else 'value is incorrect'}",
                    status_code=401,
                )

            idempotency_key = request.headers.get("Idempotency-Key")
            if idempotency_key:
                request.state.idempotency_key = idempotency_key

            return await call_next(request)

    without_authentication_endpoints = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/healthcheck",
        "/api/v1/webhooks",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        ApiKeyHeaderMiddleware,
        key_value=API_KEY,
        header_name=API_KEY_HEADER,
        ignored_endpoints=without_authentication_endpoints,
    )

    app.include_router(health_check_router, prefix="/api")
    app.include_router(payment_router, prefix="/api")
    app.include_router(webhook_router, prefix="/api")

    return app


@pytest.fixture
def test_app_with_mock_container(test_app, mock_container):
    """Создаёт TestClient с мокированным Dishka контейнером."""
    from dishka.integrations.fastapi import setup_dishka

    setup_dishka(mock_container, test_app)

    headers = {API_KEY_HEADER: API_KEY}
    with AllureTestClient(test_app, base_url="http://test", headers=headers) as c:
        yield c


@pytest.fixture
def test_app_with_container(test_app):
    """Создаёт AllureTestClient с production Dishka контейнером (для тестов с реальной БД)."""
    from dishka.integrations.fastapi import FastapiProvider, setup_dishka

    from payment_processing_service.infrastructures.ioc.di import get_providers

    container = make_async_container(*(get_providers() + [FastapiProvider()]))
    setup_dishka(container, test_app)

    headers = {API_KEY_HEADER: API_KEY}
    with AllureTestClient(test_app, base_url="http://test", headers=headers) as c:
        yield c


# ---------------------------------------------------------------------------
# Тесты: Health Check (без авторизации)
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Тесты эндпоинта /api/v1/healthcheck."""

    @pytest.mark.api
    @allure.title("Health check должен работать с API key")
    def test_health_check_with_api_key(self, test_app_with_mock_container):
        """Health check должен работать с API key."""
        response = test_app_with_mock_container.get("/api/v1/healthcheck")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Тесты: Get Payment (с авторизацией)
# ---------------------------------------------------------------------------


class TestGetPayment:
    """Тесты эндпоинта GET /api/v1/payments/{entity_id}."""

    @pytest.mark.api
    @allure.title("Получение существующего платежа должно вернуть 200")
    def test_get_payment_success(self, test_app_with_mock_container, mock_get_payment_use_case):
        """Получение существующего платежа должно вернуть 200."""
        payment_id = uuid4()

        payment_dto = PaymentDTO(
            id=payment_id,
            amount=Decimal("1500.00"),
            currency=CurrencyDTO(value=CurrencyEnum.RUB),
            description="Test payment",
            meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Test User"),
            status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
            idempotency_key="test-key",
        )
        mock_get_payment_use_case.return_value = payment_dto

        response = test_app_with_mock_container.get(f"/api/v1/payments/{payment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(payment_id)
        assert data["amount"] == "1500.00"
        assert data["currency"] == "RUB"
        assert data["status"] == "pending"

    @pytest.mark.api
    @allure.title("Запрос с невалидным ID должен вернуть 422")
    def test_get_payment_invalid_id(self, test_app_with_mock_container):
        """Запрос с невалидным ID должен вернуть 422."""
        response = test_app_with_mock_container.get("/api/v1/payments/not-a-uuid")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Тесты: Create Payment (с авторизацией)
# ---------------------------------------------------------------------------


class TestCreatePayment:
    """Тесты эндпоинта POST /api/v1/payments."""

    @pytest.mark.api
    @allure.title("Успешное создание платежа должно вернуть 202")
    def test_create_payment_success(self, test_app_with_mock_container, request, mock_create_payment_use_case):
        """Успешное создание платежа должно вернуть 202."""
        response = test_app_with_mock_container.post(
            "/api/v1/payments",
            json=VALID_PAYMENT_PAYLOAD,
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 202
        data = response.json()
        assert "payment_id" in data
        assert "status" in data
        assert "created_at" in data
        assert data["status"] == "pending"

        request.config.cache.set("test_payment_id", data["payment_id"])

    @pytest.mark.api
    @allure.title("Создание платежа без обязательных полей должно вернуть 422")
    def test_create_payment_validates_required_fields(self, test_app_with_mock_container):
        """Создание платежа без обязательных полей должно вернуть 422."""
        response = test_app_with_mock_container.post(
            "/api/v1/payments",
            json={},
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 422

    @pytest.mark.api
    @allure.title("Создание платежа с лишними полями должно вернуть 422 (extra=forbid)")
    def test_create_payment_validates_extra_fields(self, test_app_with_mock_container):
        """Создание платежа с лишними полями должно вернуть 422 (extra=forbid)."""
        payload = {**VALID_PAYMENT_PAYLOAD, "extra_field": "should_fail"}
        response = test_app_with_mock_container.post(
            "/api/v1/payments",
            json=payload,
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 422

    @pytest.mark.api
    @allure.title("Создание платежа с невалидной суммой должно вернуть 422")
    def test_create_payment_validates_amount(self, test_app_with_mock_container):
        """Создание платежа с невалидной суммой должно вернуть 422."""
        payload = {**VALID_PAYMENT_PAYLOAD, "amount": "not-a-number"}
        response = test_app_with_mock_container.post(
            "/api/v1/payments",
            json=payload,
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Тесты: Webhooks (без авторизации)
# ---------------------------------------------------------------------------


class TestWebhooks:
    """Тесты эндпоинта POST /api/v1/webhooks."""

    @pytest.mark.api
    @allure.title("Обработка вебхука должна вернуть 200")
    def test_webhook_success(self, test_app_with_mock_container, mock_process_webhook_use_case):
        """Обработка вебхука должна вернуть 200."""
        webhook_payload = {
            "payment_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "succeeded",
        }
        response = test_app_with_mock_container.post("/api/v1/webhooks", json=webhook_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.api
    @allure.title("Неудачная обработка вебхука должна вернуть 400")
    def test_webhook_failure(self, test_app_with_mock_container, mock_process_webhook_use_case):
        """Неудачная обработка вебхука должна вернуть 400."""
        mock_process_webhook_use_case.return_value = {"status": "failure", "error": "Invalid payment"}
        webhook_payload = {"payment_id": "invalid-id", "status": "unknown"}
        response = test_app_with_mock_container.post("/api/v1/webhooks", json=webhook_payload)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Тесты: Middleware
# ---------------------------------------------------------------------------


class TestMiddleware:
    """Тесты middleware (API key, error handling)."""

    @pytest.mark.api
    @allure.title("Отсутствие API key должно вернуть 401")
    def test_api_key_missing(self, test_app):
        """Отсутствие API key должно вернуть 401."""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        from payment_processing_service.presentation.api.rest.middlewares.api_key_header import (
            ApiKeyHeaderMiddleware,
        )

        test_app = FastAPI(title="Test API", version="0.1.0")
        test_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        test_app.add_middleware(ApiKeyHeaderMiddleware, key_value=API_KEY, header_name=API_KEY_HEADER)
        test_app.include_router(payment_router, prefix="/api")

        headers = {}
        with AllureTestClient(test_app, base_url="http://test", headers=headers) as c:
            response = c.get("/api/v1/payments/test")
            assert response.status_code == 401

    @pytest.mark.api
    @allure.title("Неверное значение API key должно вернуть 401")
    def test_api_key_incorrect(self, test_app):
        """Неверное значение API key должно вернуть 401."""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        from payment_processing_service.presentation.api.rest.middlewares.api_key_header import (
            ApiKeyHeaderMiddleware,
        )

        test_app = FastAPI(title="Test API", version="0.1.0")
        test_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        test_app.add_middleware(ApiKeyHeaderMiddleware, key_value=API_KEY, header_name=API_KEY_HEADER)
        test_app.include_router(payment_router, prefix="/api")

        headers = {API_KEY_HEADER: "wrong-key"}
        with AllureTestClient(test_app, base_url="http://test", headers=headers) as c:
            response = c.get("/api/v1/payments/test")
            assert response.status_code == 401


# ---------------------------------------------------------------------------
# Тесты: Response Format
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Тесты формата ответов API."""

    @pytest.mark.api
    @allure.title("Ответ должен быть в формате JSON")
    def test_payment_response_content_type(self, test_app_with_mock_container, mock_get_payment_use_case):
        """Ответ должен быть в формате JSON."""
        payment_id = uuid4()
        payment_dto = PaymentDTO(
            id=payment_id,
            amount=Decimal("1500.00"),
            currency=CurrencyDTO(value=CurrencyEnum.RUB),
            description="Test payment",
            meta_data=PaymentMetaDataDTO(address="1234567890123456", fio="Test User"),
            status=PaymentStatusDTO(value=PaymentStatusEnum.pending),
            idempotency_key="test-key",
        )
        mock_get_payment_use_case.return_value = payment_dto

        response = test_app_with_mock_container.get(f"/api/v1/payments/{payment_id}")
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.api
    @allure.title("Ответ на создание платежа должен содержать нужные поля")
    def test_create_payment_response_format(self, test_app_with_mock_container, mock_create_payment_use_case):
        """Ответ на создание платежа должен содержать нужные поля."""
        response = test_app_with_mock_container.post(
            "/api/v1/payments",
            json=VALID_PAYMENT_PAYLOAD,
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 202
        data = response.json()
        assert isinstance(data["payment_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["created_at"], str)


# ---------------------------------------------------------------------------
# Тесты: Process Payment (RabbitMQ consumer)
# ---------------------------------------------------------------------------


class TestProcessPayment:
    """Тесты обработки платежа через RabbitMQ consumer."""

    @pytest.mark.api
    @pytest.mark.timeout(15)
    @allure.title("После создания платежа RabbitMQ consumer меняет статус с pending")
    def test_process_payment_status_changed(self, request: pytest.FixtureRequest, test_app_with_container):
        """После создания платежа RabbitMQ consumer меняет статус с pending."""
        import time

        # Создаём платёж через реальный endpoint
        response = test_app_with_container.post(
            "/api/v1/payments",
            json=VALID_PAYMENT_PAYLOAD,
            headers={"Idempotency-Key": get_unique_idempotency_key()},
        )
        assert response.status_code == 202, f"Не удалось создать платёж: {response.text}"
        data = response.json()
        payment_id = data["payment_id"]
        assert data["status"] == "pending"

        request.config.cache.set("test_payment_id", payment_id)

        # Ждём пока RabbitMQ consumer обработает платёж (до 15 секунд)
        timeout = 15
        start_time = time.time()
        payment_status = None

        while time.time() - start_time < timeout:
            response = test_app_with_container.get(f"/api/v1/payments/{payment_id}")
            if response.status_code == 200:
                data = response.json()
                payment_status = data.get("status")
                if payment_status != "pending":
                    break
            time.sleep(0.5)

        assert response.status_code == 200, f"Не удалось получить платёж, статус: {response.status_code}"
        assert payment_status is not None, "Статус платежа не найден"
        assert payment_status != "pending", f"Статус платежа всё ещё pending: {payment_status}"
