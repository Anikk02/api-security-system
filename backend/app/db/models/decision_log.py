from sqlalchemy import Column, BigInteger, String, Float, DateTime
from datetime import datetime
from app.db.base import Base


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(BigInteger, primary_key=True, index=True)  # ✅ FIXED

    user_id = Column(BigInteger, index=True,nullable=True)  # ✅ FIXED

    action = Column(String, nullable=False)  # allow / throttle / block
    reason = Column(String)

    risk_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)