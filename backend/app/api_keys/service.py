from datetime import datetime
import secrets


async def get_api_key_info(db, client_id: int):
    return {
        "api_key": "sk_live_1234567890abcdef",
        "created_at": datetime.utcnow(),
        "is_active": True
    }


async def regenerate_api_key(db, client_id: int):
    return "sk_live_" + secrets.token_hex(16)