from sqlalchemy import Column, BigInteger, DateTime, String, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(BigInteger, primary_key=True, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="client")
    status = Column(String(50), nullable=False, default="active")
    email_verified = Column(Boolean, nullable=False, default=False)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_clients_status", "status"),
        Index("idx_clients_role", "role"),
    )

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
