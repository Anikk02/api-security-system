from sqlalchemy import Column, BigInteger, Float, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    user_id = Column(BigInteger, index=True, nullable=True)

    # 🔗 LINK TO REQUEST
    request_id = Column(BigInteger, ForeignKey("request_logs.id"), nullable=False)
    request_uuid = Column(String, index=True)

    # Core prediction
    risk_score = Column(Float, nullable=False)
    risk_label = Column(String)  # low / medium / high

    # Explainability
    feature_contributions = Column(JSONB)
    explanation = Column(String)

    # Model metadata
    model_version = Column(String, default="v1")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)