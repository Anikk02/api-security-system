from sqlalchemy import Column, BigInteger, DateTime
from datetime import datetime
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)  # ✅ FIXED
    created_at = Column(DateTime, default=datetime.utcnow)