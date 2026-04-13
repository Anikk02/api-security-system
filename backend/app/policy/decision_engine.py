import logging
from app.state.state_manager import StateManager
from app.risk.risk_engine import compute_risk

logger = logging.getLogger(__name__)

async def evaluate_request(identity, signals, features=None):
    '''
    Returns 
    actions: allow | throttle | block
    reason: str
    risk_score: float
    '''

    user_id = identity.user_id

    # 1. hard block ckeck
    if await StateManager.is_blocked(user_id):
        return 'block', 'User temporarily blocked', 1.0
    
    # 2. Rate Limit(State-based)
    if await StateManager.is_rate_limited(user_id):
        await StateManager.block_user(user_id, duration=3600)
        logger.warning(f"User {user_id} blocked due to rate limit")
        return 'block', 'Rate limit exceeded', 0.95
    
    # 3. Feature fallback
    if features is None:
        logger.warning("FeatureBuilder not used - falling back to signals only")
        features = {}

    # 4. Risk Engine
    try:
        risk_score = await compute_risk(signals, features)
    except Exception as e:
        logger.error(f"Rick engine failed: {e}")
        risk_score = 0.0

    # 5. Decision logic
    #strong behavioral signals
    if features.get('is_blocked'):
        return 'block', 'Behavioral block', 1.0
    
    if features.get('request_count_60s',0)>120:
        await StateManager.block_user(user_id, duration=3600)
        return 'block', 'Burst traffic detected', 0.95
    
    #ML-based decisions
    if risk_score > 0.85:
        await StateManager.block_user(user_id, duration=3600)
        return 'block', 'High risk behavior', risk_score
    
    if risk_score > 0.6:
        return 'throttle', 'Suspicious activity', risk_score
    
    return 'allow', 'Normal behavior', risk_score

