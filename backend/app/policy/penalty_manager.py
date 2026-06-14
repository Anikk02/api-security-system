import logging
import time
import hashlib
import asyncio
from app.state.state_manager import StateManager
from app.state.redis_client import redis_client

logger = logging.getLogger(__name__)

# CONFIG
WINDOWS = {
    "short": 60,        # 1 min
    "medium": 300,      # 5 min
    "long": 1800        # 30 min
}

BLOCK_DURATIONS = {
    "soft": 60 * 60 * 2,
    "medium": 60 * 60 * 6,
    "hard": 60 * 60 * 12
}

# ---------------- SAFE PARSERS ---------------- #

def _to_float(value, default=0.0):
    if value is None:
        return default
    try:
        if isinstance(value, bytes):
            value = value.decode()
        return float(value)
    except:
        return default


def _to_int(value, default=0):
    if value is None:
        return default
    try:
        if isinstance(value, bytes):
            value = value.decode()
        return int(float(value)) # handles "0.0"
    except:
        return default


# MAIN ENTRY - OPTIMIZED VERSION
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

        fingerprint = getattr(identity, "behavioral_fingerprint", None)
        if not fingerprint:
            fingerprint = _generate_fingerprint(ip, ua)

        # SINGLE pipeline for ALL reads
        pipe = redis_client.pipeline()
        
        now = time.time()
        
        # Request count
        ts_key = f"user:{user_id}:timestamps"
        pipe.zcount(ts_key, now - WINDOWS["short"], now)
        
        # Error count
        error_key = f"user:{user_id}:errors"
        pipe.get(error_key)
        
        # Violations
        violation_key = f"user:{user_id}:violations"
        pipe.get(violation_key)
        
        # Reputation keys
        rep_keys = [
            f"rep:ip:{ip}",
            f"rep:user:{user_id}",
            f"rep:fp:{fingerprint}"
        ]
        for key in rep_keys:
            pipe.get(key)
        
        # Check if IP is already blocked
        pipe.exists(f"ip:{ip}:blocked")
        pipe.exists(f"fp:{fingerprint}:blocked")
        
        # Execute all reads in ONE call
        results = await pipe.execute()
        
        # Parse results
        req_count = results[0] or 0
        error_count = int(results[1]) if results[1] else 0
        violation_count = int(results[2]) if results[2] else 0
        ip_rep = float(results[3]) if results[3] else 0.0
        user_rep = float(results[4]) if results[4] else 0.0
        fp_rep = float(results[5]) if results[5] else 0.0
        ip_already_blocked = bool(results[6]) if len(results) > 6 else False
        fp_already_blocked = bool(results[7]) if results[7] else False

        # Fast reject if IP is already blocked
        if ip_already_blocked:
            return "block", "IP is blocked", _meta(risk_score, 0)
        
        if fp_already_blocked:
            return "block", "Fingerprint is blocked", _meta(risk_score, 0)

        combined_rep = _combine_reputation(ip_rep, user_rep, fp_rep)

        # Dynamic risk boost
        adjusted_risk = min(
            risk_score * 0.7
            + combined_rep * 0.10
            + min(violation_count / 20, 0.08)
            + min(req_count / 200, 0.05)
            + min(error_count / 100, 0.07),
            1.0
        )

        # Determine action with FULL explanation
        action, reason, delta, should_block, block_severity = _determine_action_with_explanation(
            adjusted_risk, combined_rep, violation_count, risk_score, req_count, error_count
        )
        
        # SINGLE pipeline for ALL writes (fire and forget)
        asyncio.create_task(_apply_updates_pipeline(
            ip, user_id, fingerprint, rep_keys, 
            delta,should_block, block_severity, action, adjusted_risk
        ))
        
        return action, reason, _meta(adjusted_risk, combined_rep)

    except Exception as e:
        logger.error(f"Penalty V2 failed: {e}")
        return base_action, "fallback", {}


def _determine_action_with_explanation(adjusted_risk, combined_rep, violation_count, original_risk, req_count, error_count):
    """
    Determine action with detailed, user-friendly explanations.
    Returns: (action, reason, delta, should_block, block_severity)
    """
    
    # Hard rules - High reputation threat
    if combined_rep > 0.9:
        return (
            "block", 
            f"High reputation threat (reputation={combined_rep:.2f})", 
            0.2, True, "hard"
        )
    
    # Hard Block (85%+ risk)
    if adjusted_risk > 0.85:
        factors = []
        if original_risk > 0.8:
            factors.append(f"risk score {original_risk:.0%}")
        if violation_count > 5:
            factors.append(f"{violation_count} violations")
        if req_count > 100:
            factors.append(f"{req_count} requests/min")
        
        reason = f"Severe malicious activity detected" + (f" ({', '.join(factors)})" if factors else "")
        return "block", reason, 0.2, True, "hard"
    
    # Medium Block (70-85% risk)
    if adjusted_risk > 0.7 and violation_count > 3:
        return (
            "block", 
            f"Repeated suspicious behavior ({violation_count} violations in 30min)", 
            0.1, 
            True, #should_block
            "medium" # block_severity
        )
    
    if adjusted_risk > 0.7:
        # Throttle for high risk without enough violations
        factors = []
        if original_risk > 0.65:
            factors.append(f"risk spike to {original_risk:.0%}")
        if error_count > 10:
            factors.append(f"{error_count} errors")
        
        reason = f"High risk traffic" + (f" ({', '.join(factors)})" if factors else "")
        return "throttle", reason, 0.05, False, None
    
    # Throttle (50-70% risk)
    if adjusted_risk > 0.5:
        factors = []
        if original_risk > 0.55:
            factors.append(f"elevated risk {original_risk:.0%}")
        if req_count > 50:
            factors.append(f"high volume {req_count}/min")
        
        reason = f"Suspicious activity detected" + (f" ({', '.join(factors)})" if factors else "")
        return "throttle", reason, 0.05, False, None
    
    # Normal traffic
    return "allow", "Normal traffic", -0.02, False, None


async def _apply_updates_pipeline(ip, user_id, fingerprint, rep_keys, delta, should_block, block_severity, action, adjusted_risk):
    """Single pipeline for ALL updates - fire and forget"""
    try:
        pipe = redis_client.pipeline()
        
        # Update reputation keys
        for key in rep_keys:
            pipe.incrbyfloat(key, delta)
            pipe.expire(key, 3600)
        
        # Update request counter
        ts_key = f"user:{user_id}:timestamps"
        now = time.time()
        pipe.zadd(ts_key, {str(now): now})
        pipe.zremrangebyscore(ts_key, 0, now - WINDOWS["long"])
        pipe.expire(ts_key, WINDOWS["long"])
        
        # Apply block if needed
        if action == 'block' and should_block:
            duration = BLOCK_DURATIONS[block_severity]
            pipe.setex(f"user:{user_id}:blocked", duration, "1")
            pipe.setex(f"ip:{ip}:blocked", duration, "1")
            pipe.setex(f"fp:{fingerprint}:blocked", duration, "1")
            #clear throttle flag if it exist
            pipe.delete(f"user:{user_id}:throttled")
        
        # Add throttle tracking if needed
        if action == "throttle":
            #Set throttle flag for 60 seconds
            pipe.setex(f"user:{user_id}:throttled", 60, "1")
        
        else:
            #Decay throttle if it exists
            pipe.delete(f"user:{user_id}:throttled")
        
        # Store the current risk score for the next request
        pipe.setex(f"user:{user_id}:risk_score", 300, str(adjusted_risk))
        
        await pipe.execute()
        
    except Exception as e:
        logger.error(f"Background updates pipeline failed for user {user_id}: {e}")


# ---------------- HELPERS ---------------- #

def _generate_fingerprint(ip, ua):
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _combine_reputation(ip, user, fp):
    return min(1.0, (ip * 0.5 + user * 0.3 + fp * 0.2))


def _meta(risk, rep):
    return {
        "adjusted_risk": round(risk, 3),
        "reputation": round(rep, 3)
    }