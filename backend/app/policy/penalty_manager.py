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

# MAIN ENTRY - WITH IP ROTATION DETECTION
async def apply_penalty(identity, signals, risk_score: float, base_action: str):
    """
    identity → user_id, ip
    signals → request data

    Returns:
        final_action, reason, metadata
    """

    try:
        client_id = identity.client_id
        identity_id = identity.identity_id
        ip = getattr(identity, "ip_address", "unknown")
        ua = getattr(signals, "user_agent", "")
        
        # Use identity fingerprint
        fingerprint = getattr(identity, "behavioral_fingerprint", None)
        if not fingerprint:
            fingerprint = _generate_fingerprint(ip, ua)

        # Shared key namespace with StateManager
        base = StateManager._base(client_id, identity_id)

        # ✅ SINGLE pipeline for ALL reads
        pipe = redis_client.pipeline()
        
        now = time.time()
        
        # Request count
        ts_key = f"{base}:timestamps"
        pipe.zcount(ts_key, now - WINDOWS["short"], now)
        
        # Error count
        error_key = f"{base}:errors"
        pipe.get(error_key)
        
        # Violations
        violation_key = f"{base}:violations"
        pipe.get(violation_key)
        
        # ✅ IP rotation detection - get unique IP count in last 5 minutes
        ip_key = f"{base}:ips"
        pipe.scard(ip_key)  # Get count of unique IPs
        
        # Reputation keys
        rep_keys = [
            f"rep:ip:{ip}",
            f"rep:identity:{identity_id}",
            f"rep:fp:{fingerprint}"
        ]
        for key in rep_keys:
            pipe.get(key)
        
        # Check if IP is already blocked
        pipe.exists(f"ip:{ip}:blocked")
        pipe.exists(f"fp:{fingerprint}:blocked")
        pipe.exists(f"{base}:throttled")
        
        # Execute all reads in ONE call
        results = await pipe.execute()
        
        # Parse results
        req_count = _to_int(results[0])
        error_count = _to_int(results[1])
        violation_count = _to_int(results[2])
        unique_ip_count = _to_int(results[3])  # ✅ IP rotation metric
        
        ip_rep = _to_float(results[4])
        user_rep = _to_float(results[5])
        fp_rep = _to_float(results[6])
        
        ip_blocked = bool(results[7]) if len(results) > 7 else False
        fp_blocked = bool(results[8]) if results[8] else False
        throttled = bool(results[9]) if results[9] else False

        # Fast reject if already blocked
        if ip_blocked:
            return "block", "IP is blocked", _meta(risk_score, 0)
        
        if fp_blocked:
            return "block", "Fingerprint is blocked", _meta(risk_score, 0)
        
        if throttled:
            return "throttle", "Currently throttled", _meta(risk_score, 0)

        combined_rep = _combine_reputation(ip_rep, user_rep, fp_rep)

        # ✅ FIXED: Calculate IP rotation risk as a multiplier (1.0 = no impact)
        ip_rotation_multiplier = 1.0
        rotation_explanation = ""
        
        if unique_ip_count > 1:
            # Multiple IPs detected for same identity
            if unique_ip_count >= 10:
                ip_rotation_multiplier = 1.5  # 50% risk increase
                rotation_explanation = f"Extreme IP rotation ({unique_ip_count} IPs in 5min)"
            elif unique_ip_count >= 5:
                ip_rotation_multiplier = 1.3  # 30% risk increase
                rotation_explanation = f"High IP rotation ({unique_ip_count} IPs in 5min)"
            elif unique_ip_count >= 3:
                ip_rotation_multiplier = 1.15  # 15% risk increase
                rotation_explanation = f"Moderate IP rotation ({unique_ip_count} IPs in 5min)"
            else:
                ip_rotation_multiplier = 1.05  # 5% risk increase
                rotation_explanation = f"Low IP rotation ({unique_ip_count} IPs in 5min)"

        # ✅ Calculate base risk (0.0 to 0.8 range)
        base_risk = min(
            risk_score * 0.65
            + combined_rep * 0.15
            + min(violation_count / 30, 0.10)
            + min(req_count / 250, 0.05)
            + min(error_count / 150, 0.05),
            0.8  # Cap base risk at 0.8
        )
        
        # ✅ Apply IP rotation multiplier
        adjusted_risk = min(base_risk * ip_rotation_multiplier, 1.0)

        # ✅ Determine action with explanation including IP rotation
        action, reason, delta, should_block, block_severity = _determine_action_with_explanation(
            adjusted_risk, 
            combined_rep, 
            violation_count, 
            risk_score, 
            req_count, 
            error_count,
            unique_ip_count,
            rotation_explanation
        )
        
        # ✅ SINGLE pipeline for ALL writes
        asyncio.create_task(_apply_updates_pipeline(
            ip, identity_id, client_id, fingerprint, rep_keys,
            delta, should_block, block_severity, action, adjusted_risk
        ))
        
        return action, reason, _meta(adjusted_risk, combined_rep)

    except Exception as e:
        logger.error(f"Penalty V2 failed: {e}")
        return base_action, "fallback", {}


def _determine_action_with_explanation(adjusted_risk, combined_rep, violation_count, 
                                       original_risk, req_count, error_count,
                                       unique_ip_count=0, rotation_explanation=""):
    """
    Determine action with detailed, user-friendly explanations.
    """
    
    # Hard rules - High reputation threat
    if combined_rep > 0.9:
        return (
            "block", 
            f"High reputation threat (reputation={combined_rep:.2f})", 
            0.2, True, "hard"
        )
    
    # ✅ High IP rotation detected - block immediately
    if unique_ip_count >= 5 and adjusted_risk > 0.5:
        return (
            "block",
            f"IP rotation attack detected: {unique_ip_count} different IPs in 5 minutes",
            0.2, True, "hard"
        )
    
    # Medium IP rotation - throttle
    if unique_ip_count >= 3 and adjusted_risk > 0.4:
        return (
            "throttle",
            f"Suspicious IP rotation: {unique_ip_count} IPs in 5 minutes",
            0.05, False, None
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
        if unique_ip_count >= 3:
            factors.append(f"{unique_ip_count} IPs rotating")
        
        reason = f"Severe malicious activity detected" + (f" ({', '.join(factors)})" if factors else "")
        return "block", reason, 0.2, True, "hard"
    
    # Medium Block (70-85% risk)
    if adjusted_risk > 0.7 and violation_count > 3:
        return (
            "block", 
            f"Repeated suspicious behavior ({violation_count} violations in 30min)", 
            0.1, 
            True, 
            "medium"
        )
    
    if adjusted_risk > 0.7:
        # Throttle for high risk without enough violations
        factors = []
        if original_risk > 0.65:
            factors.append(f"risk spike to {original_risk:.0%}")
        if error_count > 10:
            factors.append(f"{error_count} errors")
        if unique_ip_count >= 3:
            factors.append(f"{unique_ip_count} IPs rotating")
        
        reason = f"High risk traffic" + (f" ({', '.join(factors)})" if factors else "")
        return "throttle", reason, 0.05, False, None
    
    # Throttle (50-70% risk)
    if adjusted_risk > 0.5:
        factors = []
        if original_risk > 0.55:
            factors.append(f"elevated risk {original_risk:.0%}")
        if req_count > 50:
            factors.append(f"high volume {req_count}/min")
        if unique_ip_count >= 3:
            factors.append(f"{unique_ip_count} IPs rotating")
        
        reason = f"Suspicious activity detected" + (f" ({', '.join(factors)})" if factors else "")
        return "throttle", reason, 0.05, False, None
    
    # Normal traffic
    return "allow", "Normal traffic", -0.02, False, None


async def _apply_updates_pipeline(ip, identity_id, client_id, fingerprint, rep_keys, 
                                   delta, should_block, block_severity, action, adjusted_risk):
    """Single pipeline for ALL updates - fire and forget"""
    try:
        base = StateManager._base(client_id, identity_id)
        pipe = redis_client.pipeline()
        
        # Update reputation keys
        for key in rep_keys:
            pipe.incrbyfloat(key, delta)
            pipe.expire(key, 3600)
        
        # Update request counter
        ts_key = f"{base}:timestamps"
        now = time.time()
        pipe.zadd(ts_key, {str(now): now})
        pipe.zremrangebyscore(ts_key, 0, now - WINDOWS["long"])
        pipe.expire(ts_key, WINDOWS["long"])
        
        # ✅ Track IP (already tracked by StateManager, but ensure it's done)
        ip_key = f"{base}:ips"
        pipe.sadd(ip_key, ip)
        pipe.expire(ip_key, 300)  # 5-minute window for IP rotation detection
        
        # Apply block if needed
        if action == 'block' and should_block:
            duration = BLOCK_DURATIONS[block_severity]
            pipe.setex(f"{base}:blocked", duration, "1")
            pipe.setex(f"ip:{ip}:blocked", duration, "1")
            pipe.setex(f"fp:{fingerprint}:blocked", duration, "1")
            # Clear throttle flag if it exists
            pipe.delete(f"{base}:throttled")
        
        # Add throttle tracking if needed
        if action == "throttle":
            # Set throttle flag for 60 seconds
            pipe.setex(f"{base}:throttled", 60, "1")
        else:
            # Decay throttle if it exists
            pipe.delete(f"{base}:throttled")
        
        # Store the current risk score for the next request
        pipe.setex(f"{base}:risk_score", 300, str(adjusted_risk))
        
        await pipe.execute()
        
    except Exception as e:
        logger.error(f"Background updates pipeline failed: {e}")


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