from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    full_name: str = Column(String(255), nullable=False)
    email: str = Column(String(255), unique=True, index=True, nullable=False)
    password_hash: str = Column(String(255), nullable=False)
    is_active: bool = Column(Boolean, nullable=False, server_default=text("true"))
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.utcnow,
    )

    refresh_tokens: list = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    password_resets: list = relationship(
        "PasswordReset", back_populates="user", cascade="all, delete-orphan"
    )
