from sqlalchemy import Column, BigInteger, Float, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    # ============================
    # 🔗 Request Link
    # ============================
    request_id = Column(BigInteger, ForeignKey("request_logs.id"), nullable=False)
    request_uuid = Column(String, index=True)

    # ============================
    # 🧠 Identity Layer (FIXED)
    # ============================
    identity_id = Column(String, index=True)     # 🔥 replaces user_id
    client_id = Column(Integer, index=True)      # 🔥 critical
    api_key_id = Column(Integer, nullable=True, index=True)

    # ============================
    # ⚖️ Risk Evaluation
    # ============================
    risk_score = Column(Float, nullable=False)
    risk_label = Column(String)  # low / medium / high

    # ============================
    # 📊 Explainability
    # ============================
    feature_contributions = Column(JSONB, nullable=True)
    explanation = Column(String, nullable=True)

    # ============================
    # 🧪 Model Metadata
    # ============================
    model_version = Column(String, default="v1")

    # ============================
    # ⏱️ Timestamp
    # ============================
    created_at = Column(DateTime, default=datetime.utcnow, index=True)