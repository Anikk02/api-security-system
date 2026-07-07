"""
Utility helpers used across the policy package.

This file should only contain pure utility functions.
No Redis access.
No business logic.
"""

from __future__ import annotations

import hashlib


# ==========================================================
# Safe Parsing
# ==========================================================

def to_float(value, default: float = 0.0) -> float:
    """
    Safely convert Redis values into float.
    """

    if value is None:
        return default

    try:
        if isinstance(value, bytes):
            value = value.decode()

        return float(value)

    except Exception:
        return default


def to_int(value, default: int = 0) -> int:
    """
    Safely convert Redis values into int.
    """

    if value is None:
        return default

    try:
        if isinstance(value, bytes):
            value = value.decode()

        return int(float(value))

    except Exception:
        return default


# ==========================================================
# Reputation
# ==========================================================

def combine_reputation(
    ip: float,
    identity: float,
    fingerprint: float,
) -> float:
    """
    Weighted reputation score.

    IP reputation is the strongest signal because
    malicious IPs usually affect multiple identities.
    """

    score = (
        ip * 0.50 +
        identity * 0.30 +
        fingerprint * 0.20
    )

    return min(max(score, 0.0), 1.0)


# ==========================================================
# Fingerprint
# ==========================================================

def generate_fingerprint(
    ip: str,
    user_agent: str,
) -> str:
    """
    Generate fallback fingerprint.

    Used only when middleware has not already
    generated a behavioral fingerprint.
    """

    raw = f"{ip}:{user_agent}"

    return hashlib.sha256(raw.encode()).hexdigest()


# ==========================================================
# Clamp
# ==========================================================

def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """
    Clamp value to a range.
    """

    return max(minimum, min(maximum, value))


# ==========================================================
# Linear Normalization
# ==========================================================

def normalize(
    value: float,
    max_value: float,
) -> float:
    """
    Normalize into [0,1].

    Example:

    normalize(25,100)=0.25

    normalize(150,100)=1.0
    """

    if max_value <= 0:
        return 0.0

    return clamp(value / max_value)


# ==========================================================
# Exponential Decay
# ==========================================================

def decay(
    value: float,
    factor: float,
) -> float:
    """
    Generic decay helper.

    factor=0.05

    0.60 -> 0.57
    """

    return clamp(value * (1.0 - factor))


# ==========================================================
# Risk Increase
# ==========================================================

def amplify(
    value: float,
    multiplier: float,
) -> float:
    """
    Increase risk while keeping inside [0,1].
    """

    return clamp(value * multiplier)


# ==========================================================
# Threshold Check
# ==========================================================

def between(
    value: float,
    low: float,
    high: float,
) -> bool:
    return low <= value < high