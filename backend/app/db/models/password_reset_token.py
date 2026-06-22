from sqlalchemy import (
    Column, BigInteger, String, Boolean,
    DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(BigInteger, primary_key=True, index=True)

    # Foreign key to clients
    client_id = Column(
        BigInteger,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False
    )

    # Hashed token (never store raw token)
    token_hash = Column(String(255), unique=True, nullable=False)

    # Short-lived: 15 minutes
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Single use
    used = Column(Boolean, nullable=False, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    client = relationship("Client", back_populates="password_reset_tokens")

    # Table-level indexes
    __table_args__ = (
        Index("idx_password_reset_client", "client_id", "created_at"),
        Index("idx_password_reset_expires", "expires_at"),
    )

    def __repr__(self):
        return (
            f"<PasswordResetToken(id={self.id}, client_id={self.client_id}, "
            f"used={self.used})>"
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.used and not self.is_expired
