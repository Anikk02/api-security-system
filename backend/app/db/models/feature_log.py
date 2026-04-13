from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class FeatureLog(Base):
    __tablename__ = "feature_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    user_id = Column(BigInteger, index=True, nullable=False)

    # 🔗 LINK TO REQUEST
    request_id = Column(BigInteger, ForeignKey("request_logs.id"), nullable=False)
    request_uuid = Column(String, index=True)

    # Full feature snapshot
    features = Column(JSONB, nullable=False)

    # Optional grouped features (future ML optimization)
    behavioral_features = Column(JSONB, nullable=True)
    pattern_features = Column(JSONB, nullable=True)
    identity_features = Column(JSONB, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)