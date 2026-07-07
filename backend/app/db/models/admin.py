# app/db/models/admin.py
from sqlalchemy import Column, BigInteger, DateTime, String, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(BigInteger, primary_key=True, index=True)
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="admin")  # admin, super_admin
    status = Column(String(50), nullable=False, default="active")
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    refresh_tokens = relationship(
        "AdminRefreshToken",
        back_populates="admin",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_admins_status", "status"),
        Index("idx_admins_role", "role"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"