# app/db/models/admin_refresh_token.py
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class AdminRefreshToken(Base):
    __tablename__ = "admin_refresh_tokens"

    id = Column(BigInteger, primary_key=True, index=True)
    admin_id = Column(BigInteger, ForeignKey("admins.id"), nullable=False, index=True)
    refresh_token = Column(String(512), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    admin = relationship("Admin", back_populates="refresh_tokens")