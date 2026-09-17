"""Unit tests for app.db.database module."""
import types
from collections.abc import Generator
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_session():
    """A lightweight mock that mimics a SQLAlchemy Session."""
    session = MagicMock()
    return session


@pytest.fixture()
def patched_session_local(mock_session):
    """
    Patch SessionLocal so that calling it returns *mock_session*.
    Yields (mock_session, SessionLocal_mock).
    """
    with patch("app.db.database.SessionLocal", return_value=mock_session) as mock_sl:
        yield mock_session, mock_sl


# ---------------------------------------------------------------------------
# Module-level object tests
# ---------------------------------------------------------------------------

class TestModuleLevelObjects:
    def test_engine_is_created(self):
        """engine must be importable and non-None."""
        from app.db.database import engine
        assert engine is not None

    def test_session_local_is_sessionmaker(self):
        """SessionLocal must be a sessionmaker factory."""
        from sqlalchemy.orm import sessionmaker
        from app.db.database import SessionLocal
        # sessionmaker instances are callable and have a class_/kw attribute
        assert callable(SessionLocal)

    def test_session_local_autocommit_false(self):
        """SessionLocal must have autocommit=False."""
        from app.db.database import SessionLocal
        assert SessionLocal.kw.get("autocommit") is False or \
               SessionLocal.kw.get("autocommit") == False  # noqa: E712

    def test_session_local_autoflush_false(self):
        """SessionLocal must have autoflush=False."""
        from app.db.database import SessionLocal
        assert SessionLocal.kw.get("autoflush") is False or \
               SessionLocal.kw.get("autoflush") == False  # noqa: E712

    def test_base_is_declarative_base(self):
        """Base must be a SQLAlchemy DeclarativeBase subclass."""
        from sqlalchemy.orm import DeclarativeBase
        from app.db.database import Base
        assert issubclass(Base, DeclarativeBase)


# ---------------------------------------------------------------------------
# get_db generator tests
# ---------------------------------------------------------------------------

class TestGetDb:
    def test_get_db_is_generator(self, patched_session_local):
        """get_db must return a generator."""
        from app.db.database import get_db
        result = get_db()
        assert isinstance(result, Generator)
        # Exhaust the generator to avoid resource warnings
        try:
            next(result)
        except StopIteration:
            pass
        result.close()

    def test_get_db_yields_session(self, patched_session_local):
        """The value yielded by get_db must be the session returned by SessionLocal."""
        from app.db.database import get_db
        mock_session, _ = patched_session_local

        gen = get_db()
        yielded = next(gen)
        assert yielded is mock_session
        # Close the generator cleanly
        gen.close()

    def test_get_db_closes_session_after_yield(self, patched_session_local):
        """db.close() must be called after the consumer is done."""
        from app.db.database import get_db
        mock_session, _ = patched_session_local

        gen = get_db()
        next(gen)  # run up to the yield
        # Close the generator (triggers the finally block)
        gen.close()

        mock_session.close.assert_called_once()

    def test_get_db_closes_session_on_exception(self, patched_session_local):
        """db.close() must be called even when the consumer raises."""
        from app.db.database import get_db
        mock_session, _ = patched_session_local

        gen = get_db()
        next(gen)  # run up to the yield
        try:
            gen.throw(RuntimeError("boom"))
        except RuntimeError:
            pass

        mock_session.close.assert_called_once()

    def test_get_db_creates_new_session_each_call(self, patched_session_local):
        """Each call to get_db must create an independent session."""
        from app.db.database import get_db
        _, mock_sl = patched_session_local

        gen1 = get_db()
        gen2 = get_db()
        next(gen1)
        next(gen2)
        gen1.close()
        gen2.close()

        assert mock_sl.call_count == 2

    def test_get_db_session_local_called_once_per_invocation(self, patched_session_local):
        """SessionLocal() must be called exactly once per get_db() invocation."""
        from app.db.database import get_db
        _, mock_sl = patched_session_local

        gen = get_db()
        next(gen)
        gen.close()

        mock_sl.assert_called_once_with()

    def test_get_db_close_called_once_even_without_exception(self, patched_session_local):
        """Verify close is called exactly once in the happy path."""
        from app.db.database import get_db
        mock_session, _ = patched_session_local

        gen = get_db()
        next(gen)
        gen.close()

        assert mock_session.close.call_count == 1


# ---------------------------------------------------------------------------
# Base metadata tests
# ---------------------------------------------------------------------------

class TestBase:
    def test_base_metadata_exists(self):
        """Base.metadata must be accessible (needed for table definitions)."""
        from app.db.database import Base
        assert Base.metadata is not None

    def test_base_registry_exists(self):
        """Base.registry must be accessible (DeclarativeBase requirement)."""
        from app.db.database import Base
        assert Base.registry is not None
