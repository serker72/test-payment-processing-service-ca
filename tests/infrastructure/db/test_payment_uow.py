"""Тесты для PaymentSQLAlchemyUnitOfWork."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from payment_processing_service.infrastructures.db.payment_uow import PaymentSQLAlchemyUnitOfWork


@pytest.mark.unit
class TestPaymentSQLAlchemyUnitOfWork:
    """Тесты для PaymentSQLAlchemyUnitOfWork."""

    @pytest.fixture
    def session_mock(self):
        mock = AsyncMock()
        mock.commit = AsyncMock()
        mock.rollback = AsyncMock()
        return mock

    @pytest.fixture
    def repository_mock(self):
        return MagicMock()

    @pytest.fixture
    def uow(self, session_mock, repository_mock):
        return PaymentSQLAlchemyUnitOfWork(
            session=session_mock,
            repository=repository_mock,
        )

    async def test_context_manager_enter(self, uow):
        """__aenter__ должен возвращать self."""
        async with uow as result:
            assert result is uow

    async def test_context_manager_commit_on_success(self, uow, session_mock):
        """При успешном завершении должен вызваться commit."""
        async with uow:
            pass

        session_mock.commit.assert_called_once()
        session_mock.rollback.assert_not_called()

    async def test_context_manager_rollback_on_exception(self, uow, session_mock):
        """При исключении должен вызваться rollback."""
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test error")

        session_mock.rollback.assert_called_once()
        session_mock.commit.assert_not_called()

    async def test_commit_calls_session_commit(self, uow, session_mock):
        """Метод commit должен вызвать commit сессии."""
        await uow.commit()
        session_mock.commit.assert_called_once()

    async def test_rollback_calls_session_rollback(self, uow, session_mock):
        """Метод rollback должен вызвать rollback сессии."""
        await uow.rollback()
        session_mock.rollback.assert_called_once()

    async def test_successful_exit_calls_commit(self, uow, session_mock):
        """Успешный выход из контекста должен вызвать commit."""
        async with uow:
            pass

        session_mock.commit.assert_called_once()
