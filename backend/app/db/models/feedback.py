from sqlalchemy import Column, BigInteger, Boolean, DateTime, String
from datetime import datetime
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, index=True)  # ✅ FIXED

    user_id = Column(BigInteger, index=True, nullable=True)  # ✅ FIXED

    was_blocked = Column(Boolean)
    was_correct = Column(Boolean)

    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)