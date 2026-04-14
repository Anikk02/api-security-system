import logging
from app.state.state_manager import StateManager
from app.risk.risk_engine import compute_risk

logger = logging.getLogger(__name__)

async def evaluate_request(identity, signals, features=None):
    '''
    Returns:
    action: allow | throttle | block
    reason: str
    risk_score: float
    ml_data: dict | None
    '''

    user_id = identity.user_id

    # Default ML data
    ml_data = {
        "label": None,
        "explanation": None,
        "contributions": {}
    }

    # 1. Hard block check
    if await StateManager.is_blocked(user_id):
        return 'block', 'User temporarily blocked', 1.0, ml_data

    # 2. Rate limit check (soft -> hard escalation)
    if await StateManager.is_rate_limited(user_id):
        violations = await StateManager.increment_violation(user_id)

        if violations > 3:
            await StateManager.block_user(user_id, duration=3600)
            logger.warning(f"User {user_id} blocked after repeated violations")
            return 'block', 'Repeated rate limit violations', 0.95, ml_data

        return 'throttle', 'Rate limit exceeded', 0.7, ml_data

    # 3. Feature fallback
    if features is None:
        logger.warning("FeatureBuilder not used - fallback to minimal features")
        features = {
            "request_count_60s": 0,
            "is_blocked": False
        }

    # 4. Risk Engine
    try:
        risk_score, label, explanation, contributions = await compute_risk(signals, features)
        ml_data = {
            "label": label,
            "explanation": explanation,
            "contributions": contributions
        }
    except Exception as e:
        logger.error(f"Risk engine failed: {e}")
        risk_score = 0.0

    # 5. Strong behavioral rules
    if features.get('is_blocked'):
        return 'block', 'Behavioral block', 1.0, ml_data

    if features.get('request_count_60s', 0) > 120:
        await StateManager.increment_violation(user_id)
        return 'throttle', 'Burst traffic detected', 0.8, ml_data

    # 6. ML-based decisions
    if risk_score > 0.85:
        await StateManager.increment_violation(user_id)
        await StateManager.block_user(user_id, duration=3600)
        return 'block', 'High risk behavior', risk_score, ml_data

    if risk_score > 0.6:
        await StateManager.increment_violation(user_id)
        return 'throttle', 'Suspicious activity', risk_score, ml_data

    # 7. Normal
    return 'allow', 'Normal behavior', risk_score, ml_data