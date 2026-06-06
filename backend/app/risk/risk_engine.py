import logging
from collections import deque

logger = logging.getLogger(__name__)

# CONFIG (tunable weights)
WEIGHTS = {
    'behavior': 0.4,
    'pattern': 0.35,
    'endpoint': 0.25,
}

SMOOTHED_HIGH = 0.8
SMOOTHED_MEDIUM = 0.55
RECENT_SCORES = deque(maxlen=200)

def _percentile(data, p):
    data = sorted(data)
    k = int(len(data) * p / 100)
    return data[min(k, len(data) - 1)]


def get_adaptive_thresholds():
    global SMOOTHED_HIGH, SMOOTHED_MEDIUM

    if len(RECENT_SCORES) < 30:
        return 0.70, 0.45

    data = list(RECENT_SCORES)

    dynamic_high = _percentile(data, 85)
    dynamic_medium = _percentile(data, 65)

    # Hybrid floor
    dynamic_high = max(0.70, dynamic_high)
    dynamic_medium = max(0.45, dynamic_medium)

    # Smoothing
    alpha = 0.3
    SMOOTHED_HIGH = (1 - alpha) * SMOOTHED_HIGH + alpha * dynamic_high
    SMOOTHED_MEDIUM = (1 - alpha) * SMOOTHED_MEDIUM + alpha * dynamic_medium

    # Clamp
    SMOOTHED_HIGH = min(max(SMOOTHED_HIGH, 0.70), 0.90)
    SMOOTHED_MEDIUM = min(max(SMOOTHED_MEDIUM, 0.45), 0.80)

    return SMOOTHED_HIGH, SMOOTHED_MEDIUM

# MAIN ENTRY

async def compute_risk(signals, features: dict):
    """
    Returns:
        risk_score, label, explanation, contributions
    """

    try:
        is_suspicious_ua = features.get("is_suspicious_ua", False)
        top_ratio = features.get("top_endpoint_ratio", 0.0)

        behavior_score = _behavior_risk(features)
        pattern_score = _pattern_risk(features)
        endpoint_score = _endpoint_risk(signals, features)

        risk = (
            behavior_score * WEIGHTS['behavior']
            + pattern_score * WEIGHTS['pattern']
            + endpoint_score * WEIGHTS['endpoint']
        )

        raw_score = min(risk, 1.0)

        RECENT_SCORES.append(raw_score)

        # Get adaptive thresholds
        high_th, med_th = get_adaptive_thresholds()

        # LABEL
        if raw_score > high_th:
            label = "high"
        elif raw_score > med_th:
            label = "medium"
        else:
            label = "low"

        risk_score = round(raw_score, 4)

        # EXPLANATION
        reasons = []

        if behavior_score > 0.5:
            reasons.append("Abnormal traffic spike")

        if pattern_score > 0.5:
            reasons.append("Suspicious access pattern")

        if top_ratio > 0.8:
            reasons.append("Endpoint abuse detected")

        if endpoint_score > 0.4:
            reasons.append("Sensitive endpoint access")
        
        if is_suspicious_ua:
            reasons.append("Suspicious user agent")

        explanation = ", ".join(reasons) or "Normal behavior"

        # CONTRIBUTIONS
        contributions = {
            "behavior": round(behavior_score, 3),
            "pattern": round(pattern_score, 3),
            "endpoint": round(endpoint_score, 3),
        }

        return risk_score, label, explanation, contributions

    except Exception as e:
        logger.error(f"Risk computation failed: {e}")
        return 0.0, "low", "fallback mode", {}
    
# 1. BEHAVIORAL RISK

def _behavior_risk(features: dict) -> float:

    req_count = features.get('req_per_min', 0)
    burst_ratio = features.get('burst_score', 0.0) #1.0 -> 0.0
    is_suspicious_ua = features.get("is_suspicious_ua", False)

    # Normalize
    req_score = min(req_count / 60, 1.0)
    burst_score = min(max(burst_ratio, 0.0), 1.0)

    # Combine behavior signals
    combined = 1 - (1 - req_score) * (1 - burst_score)

    # UA signal
    ua_score = 0.3 if is_suspicious_ua else 0.0

    # Fuse instead of add
    final_score = 1 - (1 - combined) * (1 - ua_score)

    return final_score


# 2. PATTERN RISK

def _pattern_risk(features: dict) -> float:

    entropy = features.get("endpoint_entropy", 0)
    top_ratio = features.get("top_endpoint_ratio", 0)

    # High entropy = attacker scanning many different endpoints
    # Low entropy = normal user revisiting a small set of pages (expected)
    #
    # Removed: repetition = 1 - (unique / total_requests)
    # Bug: that formula grows as total_requests grows regardless of actual behavior.
    # A user with 5 unique endpoints and 50 requests scores 0.9 (max bot signal),
    # identical to a real bot that hammers one endpoint.  Entropy captures scanning
    # correctly without this false positive.

    # ---Safety normalization --- #
    entropy = min(max(entropy, 0.0), 1.0)
    top_ratio = min(max(top_ratio, 0.0), 1.0)

    # --- Soft fusion (probabilistic OR) --- #
    score = 1 - (1 - entropy) * (1 - top_ratio)

    return score


# 3. ENDPOINT RISK

# Exact path matches (no substring confusion)
_SENSITIVE_EXACT = {
    "/login", "/auth", "/admin", "/payment", "/reset-password",
    "/api/data", "/api/secure",
}

# Prefix matches: endpoint must equal the prefix OR start with prefix + "/" or "?"
# e.g. "/api/admin" matches "/api/admin/users" but NOT "/api/administrator"
# e.g. "/api/user"  matches "/api/user/123"   but NOT "/api/users/me"
_SENSITIVE_PREFIXES = (
    "/api/admin",
    "/api/user",   # deliberate: /api/user/:id but NOT /api/users
    "/api/secure",
    "/api/data",
)

def _endpoint_risk(signals, features: dict) -> float:
    endpoint = getattr(signals, "endpoint", "")
    method = getattr(signals, "method", "")

    is_sensitive = False

    # Exact match
    if endpoint in _SENSITIVE_EXACT:
        is_sensitive = True
    else:
        # Prefix match: only flag /api/user/* not /api/users/*
        for prefix in _SENSITIVE_PREFIXES:
            if endpoint == prefix or endpoint.startswith(prefix + "/") or endpoint.startswith(prefix + "?"):
                is_sensitive = True
                break

    endpoint_score = 0.6 if is_sensitive else 0.0
    method_score = 0.0

    # Context-aware method risk
    if is_sensitive and method in ["POST", "PUT", "DELETE"]:
        req_rate = features.get("req_per_min", 0)
        entropy = features.get("endpoint_entropy", 0)

        if req_rate > 20 or entropy > 0.6:
            method_score = 0.4
        elif req_rate > 10:
            method_score = 0.25
        else:
            method_score = 0.1 # mild signal (not zero)

    # Soft fusion
    score = 1 - (1 - endpoint_score) * (1 - method_score)

    return score
