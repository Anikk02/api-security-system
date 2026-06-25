from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, Index
)
from datetime import datetime, timezone
from app.db.base import Base

class EmailChangeToken(Base):
    __tablename__ = "email_change_tokens"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    new_email = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)