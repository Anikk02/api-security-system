import logging
import math

logger = logging.getLogger(__name__)

#CONFIG (tunable weights)

WEIGHTS = {
    'behavior':0.4,
    'pattern': 0.3,
    'endpoint': 0.2,
    'ml': 0.1 #placeholder for future ML model
}

#MAIN ENTRY

async def compute_risk(signals, features:dict) -> float:
    '''
    Hybrid Risk Score:
    Combines rule-based + behavioral + ML signals
    
    Returns: float(0.0 -> 1.0)
    '''

    try:
        behavior_score = _behavior_risk(features)
        pattern_score = _pattern_risk(features)
        endpoint_score = _endpoint_risk(signals)
        ml_score = await _ml_risk(features)

        # Weighted aggregation
        risk = (
            behavior_score * WEIGHTS['behavior']
            + pattern_score * WEIGHTS['pattern']
            + endpoint_score * WEIGHTS['endpoint']
            + ml_score * WEIGHTS['ml']
        )

        return min(round(risk, 4), 1.0)
    
    except Exception as e:
        logger.error(f"Risk computation failed: {e}")
        return 0.0
    
# 1. BEHAVIORAL RISK

def _behavior_risk(features: dict) -> float:
    score = 0.0

    req_count = features.get('request_count_60s', 0)
    burst_ratio = features.get('burst_ratio', 1.0)
    is_blocked = features.get('is_blocked', False)

    #High request volume
    if req_count > 100:
        score += 0.6
    elif req_count > 60:
        score += 0.4
    elif req_count > 30:
        score += 0.2

    #Burst detection
    if burst_ratio > 3:
        score += 0.4
    elif burst_ratio > 2:
        score += 0.25
    
    #Already flagged user
    if is_blocked:
        score += 0.8
    
    return min(score, 1.0)

# 2. PATTERN RISK

def _pattern_risk(features: dict) -> float:
    score = 0.0

    entropy = features.get("endpoint_entropy", 0)
    repetition = features.get("repetition_score", 0)

    # High entropy = scanning attack
    if entropy > 2.5:
        score += 0.5
    elif entropy > 1.5:
        score += 0.3

    # Repeated hits (bot behavior)
    if repetition > 0.9:
        score += 0.5
    elif repetition > 0.7:
        score += 0.3

    return min(score, 1.0)

# 3. ENDPOINT RISK

def _endpoint_risk(signals) -> float:
    score = 0.0

    sensitive_endpoints = [
        "/login",
        "/auth",
        "/admin",
        "/payment",
        "/reset-password",
    ]

    if signals.endpoint in sensitive_endpoints:
        score += 0.4

    # suspicious method usage (optional)
    if hasattr(signals, "method") and signals.method == "POST":
        score += 0.1

    return min(score, 1.0)

# 4. ML RISK

async def _ml_risk(features: dict) -> float:
    """
    Placeholder for ML model:
    - Isolation Forest
    - Autoencoder
    - LSTM anomaly detection
    """

    try:
        # Example: simple anomaly heuristic for now
        anomaly_score = 0.0

        if features.get("request_count_60s", 0) > 120:
            anomaly_score += 0.5

        if features.get("endpoint_entropy", 0) > 3:
            anomaly_score += 0.4

        return min(anomaly_score, 1.0)

    except Exception as e:
        logger.error(f"ML risk failed: {e}")
        return 0.0