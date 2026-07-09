from sqlalchemy import Column, BigInteger, String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    # ============================
    # 🔗 Internal Link
    # ============================
    request_id = Column(BigInteger, ForeignKey('request_logs.id'), index=True)

    # ============================
    # 🌐 External Trace
    # ============================
    request_uuid = Column(String, index=True)

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)       # 🔥 replaces user_id
    client_id = Column(Integer, index=True)        # 🔥 critical
    api_key_id = Column(Integer, nullable=True, index=True)

    # ============================
    # ⚖️ Decision
    # ============================
    action = Column(String, nullable=False)  # allow / throttle / block
    reason = Column(String)

    risk_score = Column(Float)

    # ============================
    # 🧪 ML / Evaluation
    # ============================
    ground_truth_label = Column(String, nullable=True)

    explanation = Column(Text, nullable=True)
    explanation_json = Column(JSONB, nullable=True)

    # # ============================
    # ⏱️ Performance
    # ============================
    latency_ms = Column(Float, nullable=True)  # Fast-path latency in milliseconds


    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow, index=True)