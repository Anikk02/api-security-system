from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime
from datetime import datetime
from app.db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(BigInteger, primary_key=True, index=True)  # ✅ FIXED
    key = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(BigInteger, nullable=False)  # ✅ FIXED

    created_at = Column(DateTime, default=datetime.utcnow)