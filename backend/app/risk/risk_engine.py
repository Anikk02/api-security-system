import logging

logger = logging.getLogger(__name__)

# CONFIG (tunable weights)
WEIGHTS = {
    'behavior': 0.4,
    'pattern': 0.3,
    'endpoint': 0.2,
    'ml': 0.1
}

# MAIN ENTRY

async def compute_risk(signals, features: dict):
    """
    Returns:
        risk_score, label, explanation, contributions
    """

    try:
        behavior_score = _behavior_risk(features)
        pattern_score = _pattern_risk(features)
        endpoint_score = _endpoint_risk(signals)
        ml_score = await _ml_risk(features)

        risk = (
            behavior_score * WEIGHTS['behavior']
            + pattern_score * WEIGHTS['pattern']
            + endpoint_score * WEIGHTS['endpoint']
            + ml_score * WEIGHTS['ml']
        )

        risk_score = min(round(risk, 4), 1.0)

        # LABEL
        if risk_score > 0.85:
            label = "high"
        elif risk_score > 0.6:
            label = "medium"
        else:
            label = "low"

        # EXPLANATION
        reasons = []

        if behavior_score > 0.5:
            reasons.append("High traffic behavior")

        if pattern_score > 0.5:
            reasons.append("Suspicious access pattern")

        if endpoint_score > 0.3:
            reasons.append("Sensitive endpoint access")

        if ml_score > 0.3:
            reasons.append("ML anomaly detected")

        explanation = ", ".join(reasons) or "Normal behavior"

        # CONTRIBUTIONS
        contributions = {
            "behavior": round(behavior_score, 3),
            "pattern": round(pattern_score, 3),
            "endpoint": round(endpoint_score, 3),
            "ml": round(ml_score, 3),
        }

        return risk_score, label, explanation, contributions

    except Exception as e:
        logger.error(f"Risk computation failed: {e}")
        return 0.0, "low", "fallback mode", {}
    

# -----------------------------
# 1. BEHAVIORAL RISK
# -----------------------------

def _behavior_risk(features: dict) -> float:
    score = 0.0

    # ✅ FIXED MAPPING
    req_count = features.get('req_per_min', 0)
    burst_ratio = features.get('burst_score', 1.0)

    # High request volume
    if req_count > 100:
        score += 0.6
    elif req_count > 60:
        score += 0.4
    elif req_count > 30:
        score += 0.2

    # Burst detection
    if burst_ratio > 5:
        score += 0.4
    elif burst_ratio > 3:
        score += 0.25

    # Suspicious UA
    if features.get("is_suspicious_ua"):
        score += 0.3

    return min(score, 1.0)


# -----------------------------
# 2. PATTERN RISK
# -----------------------------

def _pattern_risk(features: dict) -> float:
    score = 0.0

    entropy = features.get("endpoint_entropy", 0)

    # ✅ derive repetition instead of missing feature
    unique = features.get("unique_endpoints", 0)
    total = features.get("req_per_min", 1)
    repetition = 1 - (unique / total) if total > 0 else 0

    # High entropy = scanning
    if entropy > 2.5:
        score += 0.5
    elif entropy > 1.5:
        score += 0.3

    # Repetition (bot behavior)
    if repetition > 0.9:
        score += 0.5
    elif repetition > 0.7:
        score += 0.3

    return min(score, 1.0)


# -----------------------------
# 3. ENDPOINT RISK
# -----------------------------

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

    if hasattr(signals, "method") and signals.method == "POST":
        score += 0.1

    return min(score, 1.0)


# -----------------------------
# 4. ML RISK (placeholder)
# -----------------------------

async def _ml_risk(features: dict) -> float:
    try:
        anomaly_score = 0.0

        # ✅ FIXED keys
        if features.get("req_per_min", 0) > 120:
            anomaly_score += 0.5

        if features.get("endpoint_entropy", 0) > 3:
            anomaly_score += 0.4

        return min(anomaly_score, 1.0)

    except Exception as e:
        logger.error(f"ML risk failed: {e}")
        return 0.0