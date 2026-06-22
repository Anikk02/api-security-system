from sqlalchemy import (
    Column, BigInteger, String, Boolean, Integer,
    DateTime, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    # Primary key
    id = Column(BigInteger, primary_key=True, index=True)

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile
    company_name = Column(String(255), nullable=True)

    # Role-based access control
    # Values: 'client', 'admin', 'super_admin'
    role = Column(String(50), nullable=False, default="client")

    # Account status
    # Values: 'active', 'inactive', 'suspended', 'locked'
    status = Column(String(50), nullable=False, default="active")

    # Email verification (optional for MVP)
    email_verified = Column(Boolean, nullable=False, default=False)

    # Brute-force protection
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Table-level indexes
    __table_args__ = (
        Index("idx_clients_status", "status"),
        Index("idx_clients_role", "role"),
    )

    def __repr__(self):
        return f"<Client(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def is_admin(self) -> bool:
        return self.role in ("admin", "super_admin")
