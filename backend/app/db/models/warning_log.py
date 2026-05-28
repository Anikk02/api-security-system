from sqlalchemy import Column, BigInteger, String, DateTime, Text
from datetime import datetime
from app.db.base import Base

class WarningLog(Base):
    __tablename__ = "warning_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)