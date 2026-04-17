import redis.asyncio as redis
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,

    # 🔥 FIXES
    max_connections=200,        # increase pool
    socket_timeout=10,
    socket_connect_timeout=10,
    retry_on_timeout=True,
    health_check_interval=30,
)