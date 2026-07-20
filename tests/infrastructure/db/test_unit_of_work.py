"""Тесты для UnitOfWork (Identity Map pattern)."""

from unittest.mock import MagicMock

import pytest

from payment_processing_service.application.interfaces.db_mapper import DbMapperProtocol
from payment_processing_service.infrastructures.db.uow import UnitOfWork, UoWModel


@pytest.mark.unit
class TestUoWModel:
    """Тесты для обёртки UoWModel."""

    def test_model_property(self):
        """Должен возвращать базовую модель."""
        model = MagicMock()
        uow = UnitOfWork()
        wrapped = UoWModel(model, uow)
        assert wrapped.model is model

    def test_getattr_delegation(self):
        """Должен делегировать доступ к атрибутам базовой модели."""
        model = MagicMock()
        model.name = "test"
        uow = UnitOfWork()
        wrapped = UoWModel(model, uow)
        assert wrapped.name == "test"

    def test_setattr_marks_dirty(self):
        """Установка атрибута должна отметить модель как dirty."""
        model = MagicMock()
        model.id = 1
        uow = UnitOfWork()
        wrapped = UoWModel(model, uow)
        wrapped.some_attr = "value"
        assert id(model) in uow.dirty


class TestUnitOfWork:
    """Тесты для UnitOfWork."""

    def test_initial_state(self):
        """Инициальное состояние должно быть пустым."""
        uow = UnitOfWork()
        assert len(uow.dirty) == 0
        assert len(uow.new) == 0
        assert len(uow.deleted) == 0
        assert len(uow.mappers) == 0

    def test_register_new(self):
        """register_new должен добавлять модель в new."""
        uow = UnitOfWork()
        model = MagicMock()
        wrapped = uow.register_new(model)

        assert id(model) in uow.new
        assert isinstance(wrapped, UoWModel)

    def test_register_dirty(self):
        """register_dirty должен добавлять модель в dirty."""
        uow = UnitOfWork()
        model = MagicMock()
        uow.register_dirty(model)

        assert id(model) in uow.dirty

    def test_register_dirty_skips_if_already_new(self):
        """register_dirty должен пропускать модель, если она уже в new."""
        uow = UnitOfWork()
        model = MagicMock()
        uow.new[id(model)] = model
        uow.register_dirty(model)

        assert len(uow.dirty) == 0
        assert id(model) in uow.new

    def test_register_deleted_removes_from_new(self):
        """register_deleted должен удалять новую модель из new (не добавлять в deleted)."""
        uow = UnitOfWork()
        model = MagicMock()
        model_id = id(model)
        uow.new[model_id] = model

        uow.register_deleted(model)

        # Новая модель удаляется из new и НЕ добавляется в deleted
        assert model_id not in uow.new
        assert model_id not in uow.deleted

    def test_register_deleted_removes_from_dirty(self):
        """register_deleted должен удалять модель из dirty и добавлять в deleted."""
        uow = UnitOfWork()
        model = MagicMock()
        model_id = id(model)
        uow.dirty[model_id] = model

        uow.register_deleted(model)

        assert model_id not in uow.dirty
        assert model_id in uow.deleted
        assert uow.deleted[model_id] is model

    def test_commit_inserts_new_models(self):
        """commit должен вставлять новые модели."""
        uow = UnitOfWork()
        mapper = MagicMock(spec=DbMapperProtocol)
        model = MagicMock()
        uow.register_mapper(type(model), mapper)
        uow.register_new(model)
        uow.commit()

        mapper.insert.assert_called_once_with(model)

    def test_commit_updates_dirty_models(self):
        """commit должен обновлять грязные модели."""
        uow = UnitOfWork()
        mapper = MagicMock(spec=DbMapperProtocol)
        model = MagicMock()
        uow.register_mapper(type(model), mapper)
        uow.register_dirty(model)
        uow.commit()

        mapper.update.assert_called_once_with(model)

    def test_commit_deletes_removed_models(self):
        """commit должен удалять удалённые модели."""
        uow = UnitOfWork()
        mapper = MagicMock(spec=DbMapperProtocol)
        model = MagicMock()
        uow.register_mapper(type(model), mapper)
        uow.register_deleted(model)
        uow.commit()

        mapper.delete.assert_called_once_with(model)

    def test_commit_clears_all_collections(self):
        """После commit все коллекции должны быть очищены."""
        uow = UnitOfWork()
        mapper = MagicMock(spec=DbMapperProtocol)
        model = MagicMock()
        uow.register_mapper(type(model), mapper)
        uow.register_new(model)
        uow.register_dirty(model)
        uow.register_deleted(model)
        uow.commit()

        assert len(uow.new) == 0
        assert len(uow.dirty) == 0
        assert len(uow.deleted) == 0

    def test_commit_raises_without_mapper(self):
        """commit должен выбросить ошибку, если нет маппера для типа модели."""
        uow = UnitOfWork()
        model = MagicMock()
        uow.register_new(model)

        with pytest.raises(ValueError, match="No mapper registered"):
            uow.commit()

    def test_clear(self):
        """clear должен очищать все коллекции."""
        uow = UnitOfWork()
        model = MagicMock()
        uow.new[id(model)] = model
        uow.dirty[id(model)] = model
        uow.deleted[id(model)] = model
        uow.clear()

        assert len(uow.new) == 0
        assert len(uow.dirty) == 0
        assert len(uow.deleted) == 0

    def test_register_mapper(self):
        """register_mapper должен регистрировать маппер для типа модели."""
        uow = UnitOfWork()
        mapper = MagicMock(spec=DbMapperProtocol)
        model = MagicMock()
        uow.register_mapper(type(model), mapper)

        assert type(model) in uow.mappers
        assert uow.mappers[type(model)] is mapper
