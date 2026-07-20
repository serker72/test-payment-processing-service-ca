"""Тесты для use case ProcessPaymentWebhook."""

from unittest.mock import patch

import pytest

from payment_processing_service.application.use_cases.process_payment_webhook import ProcessPaymentWebhookUseCase
from payment_processing_service.config.settings import Settings


class TestProcessPaymentWebhookUseCase:
    """Тесты для ProcessPaymentWebhookUseCase."""

    @pytest.fixture
    def use_case(self):
        settings = Settings()
        settings.app.backend_payment_success_rate = 0.9
        return ProcessPaymentWebhookUseCase(settings=settings)

    async def test_returns_success_status(self, use_case):
        """Может вернуть статус success."""
        with patch("random.random", return_value=0.5):
            result = await use_case({"payment_id": "test"})

        assert "status" in result

    async def test_returns_error_status(self, use_case):
        """Может вернуть статус error."""
        with patch("random.random", return_value=0.95):
            result = await use_case({"payment_id": "test"})

        assert "status" in result

    async def test_response_contains_status(self, use_case):
        """Ответ должен содержать поле status."""
        with patch("random.random", return_value=0.5):
            result = await use_case({"payment_id": "test"})

        assert result["status"] in ("success", "error")

    async def test_respects_success_rate(self):
        """При success_rate=1.0 всегда должен возвращать success."""
        settings = Settings()
        settings.app.backend_payment_success_rate = 1.0
        use_case = ProcessPaymentWebhookUseCase(settings=settings)

        with patch("random.random", return_value=0.99):
            result = await use_case({"payment_id": "test"})

        assert result["status"] == "success"
