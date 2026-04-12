from app.state.redis_client import redis_client

WINDOW_SIZE = 60
MAX_REQUESTS = 100

class StateManager:

    @staticmethod
    async def increment_request(user_id: int) -> int:
        key = f"user: {user_id}:count"

        current = await redis_client.get(key)

        if current is None:
            await redis_client.set(key, 1, ex=WINDOW_SIZE)
            return 1
        
        current = await redis_client.incr(key)
        return current
    
    @staticmethod
    async def is_rate_limited(user_id: int)-> bool:
        count = await StateManager.increment_request(user_id)
        return count> MAX_REQUESTS
    
    @staticmethod
    async def block_user(user_id: int, duration: int=3600):
        key = f"user: {user_id}: blocked"
        await redis_client.set(key, '1', ex=duration)

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        key = f"user: {user_id}:blocked"
        return await redis_client.exists(key) ==1
