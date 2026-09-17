"""Unit tests for User and RefreshToken SQLAlchemy models."""
import sys
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session

# ---------------------------------------------------------------------------
# Make sure the app package is importable regardless of how pytest is invoked.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# We need a real (in-memory) database so that SQLAlchemy can resolve
# relationships and column defaults without a running PostgreSQL instance.
from sqlalchemy import event

# Patch the Base import so that our models share the same metadata.
import importlib, types

# ------------------------------------------------------------------
# Minimal stub for app.db.database so we can import models standalone
# ------------------------------------------------------------------
from sqlalchemy.orm import declarative_base

_Base = declarative_base()

# Inject stub module before importing models
db_mod = types.ModuleType("app.db.database")
db_mod.Base = _Base
app_mod = types.ModuleType("app")
app_db_mod = types.ModuleType("app.db")
sys.modules.setdefault("app", app_mod)
sys.modules.setdefault("app.db", app_db_mod)
sys.modules["app.db.database"] = db_mod

# Now import models (they will pick up the stubbed Base)
from app.models.user import User  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: E402

# ------------------------------------------------------------------
# In-memory SQLite engine & session factory
# ------------------------------------------------------------------
ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    echo=False,
)

# SQLite does not support server_default text('now()') natively, but we only
# need the ORM layer behaviour; we create the schema without relying on those.
_Base.metadata.create_all(ENGINE)

SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


@pytest.fixture()
def db() -> Session:
    """Yield a transactional session that is rolled back after each test."""
    connection = ENGINE.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ===========================================================================
# Helper factories
# ===========================================================================

def make_user(**kwargs) -> User:
    defaults = dict(
        full_name="Alice Smith",
        email="alice@example.com",
        password_hash="hashed_password_value",
        is_active=True,
    )
    defaults.update(kwargs)
    return User(**defaults)


def make_refresh_token(user_id: int, **kwargs) -> RefreshToken:
    defaults = dict(
        user_id=user_id,
        token_hash="some_token_hash",
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        remember_me=False,
    )
    defaults.update(kwargs)
    return RefreshToken(**defaults)


# ===========================================================================
# User model – column / table structure
# ===========================================================================

class TestUserModelStructure:
    """Inspect column definitions via SQLAlchemy introspection."""

    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_primary_key_column(self):
        col = User.__table__.c["id"]
        assert col.primary_key

    def test_full_name_not_nullable(self):
        col = User.__table__.c["full_name"]
        assert not col.nullable

    def test_email_unique(self):
        col = User.__table__.c["email"]
        assert col.unique

    def test_email_not_nullable(self):
        col = User.__table__.c["email"]
        assert not col.nullable

    def test_password_hash_not_nullable(self):
        col = User.__table__.c["password_hash"]
        assert not col.nullable

    def test_is_active_not_nullable(self):
        col = User.__table__.c["is_active"]
        assert not col.nullable

    def test_created_at_not_nullable(self):
        col = User.__table__.c["created_at"]
        assert not col.nullable

    def test_updated_at_not_nullable(self):
        col = User.__table__.c["updated_at"]
        assert not col.nullable

    def test_refresh_tokens_relationship_exists(self):
        assert hasattr(User, "refresh_tokens")

    def test_password_resets_relationship_exists(self):
        assert hasattr(User, "password_resets")


# ===========================================================================
# User model – ORM behaviour
# ===========================================================================

class TestUserModelORM:
    def test_create_and_retrieve_user(self, db):
        user = make_user()
        db.add(user)
        db.flush()

        retrieved = db.query(User).filter_by(email="alice@example.com").one()
        assert retrieved.full_name == "Alice Smith"
        assert retrieved.email == "alice@example.com"
        assert retrieved.password_hash == "hashed_password_value"
        assert retrieved.is_active is True

    def test_user_id_is_assigned_on_flush(self, db):
        user = make_user()
        db.add(user)
        db.flush()
        assert user.id is not None
        assert isinstance(user.id, int)

    def test_two_users_different_ids(self, db):
        u1 = make_user(email="a@example.com")
        u2 = make_user(email="b@example.com")
        db.add_all([u1, u2])
        db.flush()
        assert u1.id != u2.id

    def test_duplicate_email_raises(self, db):
        """Unique constraint on email must be enforced."""
        from sqlalchemy.exc import IntegrityError

        db.add(make_user(email="dup@example.com"))
        db.flush()
        db.add(make_user(email="dup@example.com"))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_missing_full_name_raises(self, db):
        from sqlalchemy.exc import IntegrityError

        user = User(email="noname@example.com", password_hash="x", is_active=True)
        db.add(user)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_missing_email_raises(self, db):
        from sqlalchemy.exc import IntegrityError

        user = User(full_name="No Email", password_hash="x", is_active=True)
        db.add(user)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_refresh_tokens_list_initially_empty(self, db):
        user = make_user()
        db.add(user)
        db.flush()
        assert user.refresh_tokens == []

    def test_password_resets_list_initially_empty(self, db):
        user = make_user()
        db.add(user)
        db.flush()
        assert user.password_resets == []

    def test_is_active_can_be_false(self, db):
        user = make_user(is_active=False)
        db.add(user)
        db.flush()
        retrieved = db.query(User).filter_by(email="alice@example.com").one()
        assert retrieved.is_active is False

    def test_user_repr_does_not_raise(self):
        """Instantiating and converting to str should never raise."""
        user = make_user()
        _ = str(user)  # should not raise


# ===========================================================================
# RefreshToken model – column / table structure
# ===========================================================================

class TestRefreshTokenModelStructure:
    def test_tablename(self):
        assert RefreshToken.__tablename__ == "refresh_tokens"

    def test_primary_key(self):
        assert RefreshToken.__table__.c["id"].primary_key

    def test_user_id_not_nullable(self):
        assert not RefreshToken.__table__.c["user_id"].nullable

    def test_token_hash_not_nullable(self):
        assert not RefreshToken.__table__.c["token_hash"].nullable

    def test_token_hash_unique(self):
        assert RefreshToken.__table__.c["token_hash"].unique

    def test_expires_at_not_nullable(self):
        assert not RefreshToken.__table__.c["expires_at"].nullable

    def test_revoked_at_nullable(self):
        assert RefreshToken.__table__.c["revoked_at"].nullable

    def test_remember_me_not_nullable(self):
        assert not RefreshToken.__table__.c["remember_me"].nullable

    def test_created_at_not_nullable(self):
        assert not RefreshToken.__table__.c["created_at"].nullable

    def test_user_relationship_exists(self):
        assert hasattr(RefreshToken, "user")

    def test_user_id_foreign_key_references_users(self):
        fk = list(RefreshToken.__table__.c["user_id"].foreign_keys)[0]
        assert "users.id" in str(fk.target_fullname)


# ===========================================================================
# RefreshToken model – ORM behaviour
# ===========================================================================

class TestRefreshTokenModelORM:
    def _create_user(self, db) -> User:
        user = make_user()
        db.add(user)
        db.flush()
        return user

    def test_create_and_retrieve_token(self, db):
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id)
        db.add(token)
        db.flush()

        retrieved = db.query(RefreshToken).filter_by(token_hash="some_token_hash").one()
        assert retrieved.user_id == user.id
        assert retrieved.expires_at == datetime(2099, 1, 1, tzinfo=timezone.utc)
        assert retrieved.revoked_at is None
        assert retrieved.remember_me is False

    def test_token_id_assigned_on_flush(self, db):
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id)
        db.add(token)
        db.flush()
        assert token.id is not None

    def test_duplicate_token_hash_raises(self, db):
        from sqlalchemy.exc import IntegrityError

        user = self._create_user(db)
        db.add(make_refresh_token(user_id=user.id, token_hash="same_hash"))
        db.flush()

        user2 = make_user(email="bob@example.com")
        db.add(user2)
        db.flush()
        db.add(make_refresh_token(user_id=user2.id, token_hash="same_hash"))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_revoked_at_can_be_set(self, db):
        user = self._create_user(db)
        revocation_time = datetime(2030, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        token = make_refresh_token(user_id=user.id, revoked_at=revocation_time)
        db.add(token)
        db.flush()

        retrieved = db.query(RefreshToken).filter_by(token_hash="some_token_hash").one()
        assert retrieved.revoked_at == revocation_time

    def test_remember_me_true(self, db):
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id, remember_me=True)
        db.add(token)
        db.flush()

        retrieved = db.query(RefreshToken).get(token.id)
        assert retrieved.remember_me is True

    def test_relationship_back_to_user(self, db):
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id)
        db.add(token)
        db.flush()
        db.refresh(token)

        assert token.user is not None
        assert token.user.id == user.id

    def test_user_has_token_via_relationship(self, db):
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id)
        db.add(token)
        db.flush()
        db.refresh(user)

        assert len(user.refresh_tokens) == 1
        assert user.refresh_tokens[0].token_hash == "some_token_hash"

    def test_cascade_delete_removes_tokens(self, db):
        """Deleting a User should cascade-delete its RefreshTokens."""
        user = self._create_user(db)
        token = make_refresh_token(user_id=user.id)
        db.add(token)
        db.flush()
        token_id = token.id

        db.delete(user)
        db.flush()

        assert db.query(RefreshToken).filter_by(id=token_id).first() is None

    def test_multiple_tokens_same_user(self, db):
        user = self._create_user(db)
        t1 = make_refresh_token(user_id=user.id, token_hash="hash_one")
        t2 = make_refresh_token(user_id=user.id, token_hash="hash_two")
        db.add_all([t1, t2])
        db.flush()
        db.refresh(user)

        assert len(user.refresh_tokens) == 2
