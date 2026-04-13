from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from datetime import datetime
from app.db.base import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(BigInteger, primary_key=True, index=True)  # ✅ FIXED

    user_id = Column(BigInteger, index=True,nullable=True)  # ✅ FIXED
    endpoint = Column(String, nullable=False)

    ip_address = Column(String)
    user_agent = Column(String)

    status_code = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)