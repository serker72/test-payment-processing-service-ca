from typing import final


class RepositoryNotFoundError(Exception):
    """Исключение возникает при отсутствии записи в репозитории."""


class RepositorySaveError(Exception):
    """Исключение возникает при сохранении данных в репозиторий."""


@final
class RepositoryConflictError(Exception):
    """Исключение возникает при конфликте во время работы репозитория."""
