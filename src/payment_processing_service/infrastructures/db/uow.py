from typing import Any, Dict, Type, TypeVar

from loguru import logger

from payment_processing_service.application.interfaces.db_mapper import DbMapperProtocol

T = TypeVar("T")


class UoWModel:
    """Класс обёртки для моделей, отслеживаемых по Unit of Work."""

    def __init__(self, model: T, uow: "UnitOfWork"):
        self._model = model
        self._uow = uow

    @property
    def model(self) -> T:
        """Получает базовую модель."""
        return self._model

    def __getattr__(self, name: str) -> Any:
        """Делегирует доступ к атрибуту базовой модели."""
        return getattr(self._model, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Делегирует настройку атрибута базовой модели и отметить как грязный."""
        if name in ("_model", "_uow"):
            super().__setattr__(name, value)
        else:
            setattr(self._model, name, value)
            self._uow.register_dirty(self._model)


class UnitOfWork:
    """Реализация Unit of Work по шаблону Identity Map."""

    def __init__(self):
        self.dirty: Dict[int, Any] = {}
        self.new: Dict[int, Any] = {}
        self.deleted: Dict[int, Any] = {}
        self.mappers: Dict[Type[Any], DbMapperProtocol[Any]] = {}

    def register_dirty(self, model: Any) -> None:
        """Регистрирует модель как грязную (модифицированную)."""
        model_id = id(model)
        if model_id in self.new:
            return
        self.dirty[model_id] = model
        logger.debug(f"Registered model {model_id} as dirty")

    def register_deleted(self, model: Any) -> None:
        """Регистрирует модель как удаленную."""
        if isinstance(model, UoWModel):
            model = model._model

        model_id = id(model)
        if model_id in self.new:
            self.new.pop(model_id)
            return
        if model_id in self.dirty:
            self.dirty.pop(model_id)
        self.deleted[model_id] = model
        logger.debug(f"Registered model {model_id} as deleted")

    def register_new(self, model: Any) -> UoWModel:
        """Регистрирует новую модель и возвращает обёртку UoWModel."""
        model_id = id(model)
        self.new[model_id] = model
        logger.debug(f"Registered new model {model_id}")
        return UoWModel(model, self)

    def commit(self) -> None:
        """Фиксирует все изменения в базе данных."""
        logger.debug("Starting commit process")

        for model in self.new.values():
            model_type = type(model)
            if model_type not in self.mappers:
                raise ValueError(f"No mapper registered for type {model_type}")
            self.mappers[model_type].insert(model)
            logger.debug(f"Inserted model of type {model_type}")

        for model in self.dirty.values():
            model_type = type(model)
            if model_type not in self.mappers:
                raise ValueError(f"No mapper registered for type {model_type}")
            self.mappers[model_type].update(model)
            logger.debug(f"Updated model of type {model_type}")

        for model in self.deleted.values():
            model_type = type(model)
            if model_type not in self.mappers:
                raise ValueError(f"No mapper registered for type {model_type}")
            self.mappers[model_type].delete(model)
            logger.debug(f"Deleted model of type {model_type}")

        self.clear()
        logger.debug("Commit completed successfully")

    def clear(self) -> None:
        """Очищает все отслеживаемые модели."""
        self.dirty.clear()
        self.new.clear()
        self.deleted.clear()
        logger.debug("Cleared all tracked models")

    def register_mapper(self, model_type: Type[T], mapper: DbMapperProtocol[T]) -> None:
        """Регистрирует маппер для конкретного типа модели."""
        self.mappers[model_type] = mapper
        logger.debug(f"Registered mapper for type {model_type}")
