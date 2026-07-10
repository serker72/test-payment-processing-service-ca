from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True, order=True)
class BaseEntity:
    id: int | None = None

    # Поля аудита
    created_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = field(default_factory=lambda: datetime.now(UTC))

    def is_new(self) -> bool:
        """Проверяет, является ли сущность новой."""
        return self.id is None
