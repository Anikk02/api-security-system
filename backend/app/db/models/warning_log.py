from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, ForeignKey
from datetime import datetime
from app.db.base import Base


class WarningLog(Base):
    __tablename__ = "warning_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    # ============================
    # 🔗 Optional request link
    # ============================
    request_id = Column(BigInteger, ForeignKey("request_logs.id"), nullable=True, index=True)

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)     # 🔥 replaces user_id
    client_id = Column(Integer, index=True)      # 🔥 critical
    api_key_id = Column(Integer, nullable=True, index=True)

    # ============================
    # ⚠️ Warning Details
    # ============================
    message = Column(Text, nullable=False)
    level = Column(String, default="medium")  # low / medium / high

    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow)