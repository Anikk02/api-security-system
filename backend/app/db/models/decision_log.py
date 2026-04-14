from sqlalchemy import Column, BigInteger, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    #internal FK
    request_id = Column(BigInteger, ForeignKey('request_logs.id'), index=True)

    #External trace
    request_uuid = Column(String, index=True)

    user_id = Column(BigInteger, index=True,nullable=True) 


    action = Column(String, nullable=False)  # allow / throttle / block
    reason = Column(String)

    risk_score = Column(Float)

    ground_truth_label = Column(String, nullable=True)

    explanation = Column(Text)

    explanation_json = Column(JSONB)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)