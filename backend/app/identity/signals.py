import logging
from fastapi import Request
from datetime import datetime

logger = logging.getLogger(__name__)

class RequestSignals:
    def __init__(
            self,
            ip_address: str,
            user_agent: str,
            endpoint: str,
            method: str,
            timestamp: datetime
    ):
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.endpoint = endpoint
        self.method = method
        self.timestamp = timestamp

async def extract_signals(request: Request) -> RequestSignals:
    # ✅ FIX: Support X-Forwarded-For (for simulation + proxies)
    forwarded_ip = request.headers.get("X-Forwarded-For")

    if forwarded_ip:
        # take first IP (real client IP in proxy chain)
        ip = forwarded_ip.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else 'unknown'

    user_agent = request.headers.get("user-agent", "unknown")

    endpoint = request.url.path
    method = request.method
    timestamp = datetime.utcnow()

    logger.info(f"{method} {endpoint} | IP={ip}")

    return RequestSignals(
        ip_address=ip,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        timestamp=timestamp
    )