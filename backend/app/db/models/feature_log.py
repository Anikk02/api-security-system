from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class FeatureLog(Base):
    __tablename__ = "feature_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # ============================
    # 🔗 Link to request
    # ============================
    request_id = Column(BigInteger, ForeignKey("request_logs.id"), nullable=False)
    request_uuid = Column(String, index=True)

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)      # 🔥 replaces user_id
    client_id = Column(Integer, index=True)       # 🔥 critical
    api_key_id = Column(Integer, nullable=True, index=True)

    # ============================
    # 📊 Feature Snapshots
    # ============================
    features = Column(JSONB, nullable=False)

    # Optional grouping (ML optimization)
    behavioral_features = Column(JSONB, nullable=True)
    pattern_features = Column(JSONB, nullable=True)
    identity_features = Column(JSONB, nullable=True)

    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow, index=True)