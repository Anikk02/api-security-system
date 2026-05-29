import logging
from app.state.state_manager import StateManager
from app.risk.risk_engine import compute_risk
from app.policy.penalty_manager import apply_penalty
from app.explainability.explainer import Explainer

logger = logging.getLogger(__name__)

SAFE_ENDPOINTS = ["/api/dashboard", "/health"]

async def evaluate_request(identity, signals, features=None):
    '''
    Returns:
    action: allow | throttle | block
    reason: str
    risk_score: float
    ml_data: dict | None
    '''
    user_id = identity.user_id
     # ============ DASHBOARD BYPASS ============
    # Skip ALL security checks for dashboard and health endpoints
    if any(signals.endpoint.startswith(e) for e in SAFE_ENDPOINTS):
        return 'allow', 'Dashboard bypass', 0.0, {}

    # 1. Hard block check
    if await StateManager.is_blocked(user_id):
        return 'block', 'User temporarily blocked', 1.0, ml_data

    # 2. Rate limit check (ONLY signal, no punishment)
    if await StateManager.is_rate_limited(user_id):
        base_action = 'throttle'
        base_reason = 'Rate limit exceeded'
    else:
        base_action = None
        base_reason = None

    # 3. Feature fallback (UNCHANGED as requested)
    if features is None:
        logger.warning("FeatureBuilder not used - fallback to minimal features")
        features = {
            "req_per_min": 0,
            "is_blocked": False
        }

    ml_data = {
        "label": None,
        "explanation": None,
        "contributions": {}
    }

    # 4. Risk Engine
    try:
        risk_score, label, risk_explanation, contributions = await compute_risk(signals, features)

        ml_data = {
            "label": label,
            "explanation": risk_explanation,
            "contributions": contributions
        }

    except Exception as e:
        logger.error(f"Risk engine failed: {e}")
        risk_score = 0.0

    # 5. Base decision (only if not preset)
    if base_action is None:
        # Behavioral block signal
        if features.get('is_blocked'):
            base_action = 'block'
            base_reason = 'Behavioral block'

        # Traffic burst
        elif features.get('req_per_min', 0) > 80:
            base_action = 'throttle'
            base_reason = 'High traffic burst'

        # ML-based decisions
        elif risk_score > 0.7:
            base_action = 'throttle'
            base_reason = 'High risk detected'

        elif risk_score > 0.4:
            base_action = 'throttle'
            base_reason = 'Suspicious activity'

        elif risk_score > 0.2:
            base_action = 'allow'
            base_reason = 'Low risk anomaly'

        else:
            base_action = 'allow'
            base_reason = 'Normal behavior'

    # 6. Penalty Manager (FINAL AUTHORITY)
    try:
        final_action, penalty_reason, meta = await apply_penalty(
            identity=identity,
            signals=signals,
            risk_score=risk_score,
            base_action=base_action
        )

    except Exception as e:
        logger.error(f"Penalty manager failed: {e}")

        final_action = base_action
        penalty_reason = base_reason
        meta = {}

    # EXPLAINABILITY
    explanation = Explainer.generate(
        action=final_action,
        reason=penalty_reason or base_reason,
        risk_score=risk_score,
        features=features,
        ml_data=ml_data
    )

    # FINAL RESPONSE
    return (
        final_action,
        penalty_reason or base_reason,
        risk_score,
        {
            **ml_data,
            "penalty_meta": meta,
            "explanation": explanation
        }
    )