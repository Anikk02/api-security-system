from sqlalchemy import (
    Column, BigInteger, String, Boolean,
    DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Revocation
    revoked = Column(Boolean, nullable=False, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Session/device tracking
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    client = relationship("Client", back_populates="refresh_tokens")

    # Table-level indexes
    __table_args__ = (
        Index("idx_refresh_tokens_client_id", "client_id"),
        Index("idx_refresh_tokens_expires", "expires_at"),
    )

    def __repr__(self):
        return (
            f"<RefreshToken(id={self.id}, client_id={self.client_id}, "
            f"revoked={self.revoked})>"
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.revoked and not self.is_expired
