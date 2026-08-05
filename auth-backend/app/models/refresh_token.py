from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship

from app.db.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: str = Column(String(255), nullable=False, unique=True, index=True)
    expires_at: datetime = Column(DateTime(timezone=True), nullable=False)
    revoked_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    remember_me: bool = Column(Boolean, nullable=False, server_default=text("false"))
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user = relationship("User", back_populates="refresh_tokens")
