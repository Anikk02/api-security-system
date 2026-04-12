import logging
from app.state.state_manager import StateManager
from app.risk.risk_engine import compute_risk

logger = logging.getLogger(__name__)

async def evaluate_request(identity, signals):
    """
    Returns:
    actions: allow | throttle | block
    reason: str
    risk_score: float
    """

    # Check block state
    if await StateManager.is_blocked(identity.user_id):
        return "block", "User temporarily blocked",1.0
    
    # Rate limiting
    if await StateManager.is_rate_limited(identity.user_id):
        await StateManager.block_user(identity.user_id, duration=3600)
        logger.warning(f"User {identity.user_id} blocked due to rate limit")
        return 'block', 'Rate limit exceeded', 0.9
    
    # Risk (ML Placeholder)
    risk_score = await compute_risk(signals)

    if risk_score>0.8:
        await StateManager.block_user(identity.user_id, duration=3600)
        return 'block', 'High risk behavior', risk_score
    
    if risk_score > 0.5:
        return 'throttle', 'Suspicious activity', risk_score
    
    return 'allow', 'Normal behavior', risk_score