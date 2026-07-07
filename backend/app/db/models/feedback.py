from sqlalchemy import Column, BigInteger, Boolean, DateTime, String, ForeignKey, Integer
from datetime import datetime
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True, index=True)

    # ============================
    # 🔗 Link to decision (CRITICAL)
    # ============================
    decision_id = Column(BigInteger, ForeignKey("decision_logs.id"), index=True)

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)     # replaces user_id
    client_id = Column(Integer, index=True)

    # ============================
    # ⚖️ Feedback Signals
    # ============================
    was_blocked = Column(Boolean)   # system decision
    was_correct = Column(Boolean)   # human validation

    notes = Column(String)

    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow)