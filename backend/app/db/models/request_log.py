from sqlalchemy import Column, BigInteger, String, DateTime, Integer, ForeignKey
from datetime import datetime
from app.db.base import Base
import uuid


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    # ============================
    # 🌐 External tracing
    # ============================
    request_uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)       # 🔥 replaces user_id
    client_id = Column(Integer, index=True)        # 🔥 critical
    api_key_id = Column(Integer, nullable=True, index=True)

    # ============================
    # 🌍 Request Metadata
    # ============================
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=True)

    ip_address = Column(String)
    user_agent = Column(String)

    # ============================
    # ⚖️ Result
    # ============================
    status_code = Column(Integer)
    action = Column(String)   # allow / block / throttle

    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow, index=True)