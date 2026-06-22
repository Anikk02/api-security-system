from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime, Boolean
from datetime import datetime
from app.db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(BigInteger, primary_key=True, index=True) 
    key = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False, default="Default Key")
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)