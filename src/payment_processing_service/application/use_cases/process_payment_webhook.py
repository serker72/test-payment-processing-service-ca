import random
from dataclasses import dataclass
from typing import final

from payment_processing_service.config.settings import Settings


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessPaymentWebhookUseCase:
    """Сценарий обработки вебхука для платежа."""

    settings: Settings

    async def __call__(self, data: dict) -> dict:
        """Выполняет сценарий обработки вебхука для платежа."""
        return {"status": "error" if random.random() >= self.settings.app.backend_payment_success_rate else "success"}
