from sqlalchemy import Column, BigInteger, String, DateTime, Integer
from datetime import datetime
from app.db.base import Base
import uuid


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(BigInteger, primary_key=True, index=True) 

    #External tracing ID
    request_uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(BigInteger, index=True,nullable=True) 
    endpoint = Column(String, nullable=False)

    ip_address = Column(String)
    user_agent = Column(String)

    status_code = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)