from abc import abstractmethod
from typing import Protocol, TypeVar

T = TypeVar("T")


class DbMapperProtocol(Protocol[T]):
    """Протокол для преобразования данных в БД, используемый в Unit of Work."""

    @abstractmethod
    def insert(self, model: T) -> None:
        """Вставляет новую модель в базу данных."""

    @abstractmethod
    def update(self, model: T) -> None:
        """Обновляет существующую модель в базе данных."""

    @abstractmethod
    def delete(self, model: T) -> None:
        """Удаляет модель из базы данных."""
