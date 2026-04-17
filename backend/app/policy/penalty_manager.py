import logging
import time
import hashlib

from app.state.state_manager import StateManager

logger = logging.getLogger(__name__)

# CONFIG
WINDOWS = {
    "short": 60,        # 1 min
    "medium": 300,      # 5 min
    "long": 1800        # 30 min
}

BLOCK_DURATIONS = {
    "soft": 60 * 2,
    "medium": 60 * 10,
    "hard": 60 * 60
}


# MAIN ENTRY
async def apply_penalty(identity, signals, risk_score: float, base_action: str):
    """
    identity → user_id, ip
    signals → request data

    Returns:
        final_action, reason, metadata
    """

    try:
        user_id = identity.user_id
        ip = getattr(identity, "ip_address", "unknown")
        ua = getattr(signals, "user_agent", "")

        fingerprint = _generate_fingerprint(ip, ua)

        now = time.time()

        # 🔹 1. Sliding window counters
        # Requests per IP (reuse timestamps logic via user_id OR create IP-based key)
        req_count = await StateManager.get_request_count(user_id, WINDOWS["short"])

        # Errors (already tracked)
        error_count = await StateManager.get_error_count(user_id, WINDOWS["medium"])

        # Violations (already implemented)
        violation_count = await StateManager.get_violations(user_id)

        # 🔹 2. Reputation scores
        ip_rep = await _get_reputation(f"rep:ip:{ip}")
        user_rep = await _get_reputation(f"rep:user:{user_id}")
        fp_rep = await _get_reputation(f"rep:fp:{fingerprint}")

        combined_rep = _combine_reputation(ip_rep, user_rep, fp_rep)

        # 🔹 3. Dynamic risk boost
        adjusted_risk = min(
            risk_score * 0.6
            + combined_rep * 0.2
            + min(req_count / 200, 0.1)
            + min(error_count / 100, 0.1),
            1.0
        )

        # 🔹 4. Hard rules (fast path)
        if combined_rep > 0.9:
            await _block(ip, user_id, "hard")
            return "block", "High reputation threat", _meta(adjusted_risk, combined_rep)

        # 🔹 5. Escalation logic

        # 🔴 HARD BLOCK
        if adjusted_risk > 0.85:
            await _increase_reputation(ip, user_id, fingerprint, 0.2)
            await _block(ip, user_id, "hard")

            return "block", "Severe malicious activity", _meta(adjusted_risk, combined_rep)

        # 🔴 MEDIUM BLOCK
        if adjusted_risk > 0.7:
            await _increase_reputation(ip, user_id, fingerprint, 0.1)

            if violation_count > 3:
                await _block(ip, user_id, "medium")
                return "block", "Repeated suspicious behavior", _meta(adjusted_risk, combined_rep)

            return "throttle", "High risk traffic", _meta(adjusted_risk, combined_rep)

        # 🟡 THROTTLE
        if adjusted_risk > 0.5:
            await _increase_reputation(ip, user_id, fingerprint, 0.05)
            return "throttle", "Suspicious activity", _meta(adjusted_risk, combined_rep)

        # 🟢 SAFE
        await _decay_reputation(ip, user_id, fingerprint)
        return base_action, "Normal traffic", _meta(adjusted_risk, combined_rep)

    except Exception as e:
        logger.error(f"Penalty V2 failed: {e}")
        return base_action, "fallback", {}


# ---------------- HELPERS ---------------- #

def _generate_fingerprint(ip, ua):
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _get_reputation(key):
    value = await StateManager.get(key)
    return float(value) if value else 0.0


async def _increase_reputation(ip, user_id, fp, delta):
    await _update_rep(f"rep:ip:{ip}", delta)
    await _update_rep(f"rep:user:{user_id}", delta)
    await _update_rep(f"rep:fp:{fp}", delta)


async def _decay_reputation(ip, user_id, fp):
    await _update_rep(f"rep:ip:{ip}", -0.02)
    await _update_rep(f"rep:user:{user_id}", -0.02)
    await _update_rep(f"rep:fp:{fp}", -0.02)


async def _update_rep(key, delta):
    val = await _get_reputation(key)
    val = max(0.0, min(val + delta, 1.0))
    await StateManager.set(key, val, ttl=3600)


def _combine_reputation(ip, user, fp):
    return min(1.0, (ip * 0.5 + user * 0.3 + fp * 0.2))


async def _block(ip, user_id, severity):
    duration = BLOCK_DURATIONS[severity]

    await StateManager.block_user(user_id, duration)
    await StateManager.block_ip(ip, duration)


def _meta(risk, rep):
    return {
        "adjusted_risk": round(risk, 3),
        "reputation": round(rep, 3)
    }