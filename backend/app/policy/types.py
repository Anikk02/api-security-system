"""
Shared types used by the Policy Engine.

This module intentionally contains only:
- Enums
- Type aliases
- Protocols
- TypedDicts (optional)

No business logic should live here.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol, TypedDict


# ==========================================================
# Action Types
# ==========================================================

Action = Literal[
    "allow",
    "throttle",
    "block",
]


BlockSeverity = Literal[
    "soft",
    "medium",
    "hard",
]


# ==========================================================
# Decision Reasons
# ==========================================================

class DecisionReason(str, Enum):
    NORMAL = "normal"

    HIGH_RISK = "high_risk"

    HIGH_REPUTATION = "high_reputation"

    REPEATED_VIOLATIONS = "repeated_violations"

    IP_ROTATION = "ip_rotation"

    RATE_LIMIT = "rate_limit"

    ERROR_SPIKE = "error_spike"

    THROTTLED = "throttled"

    BLOCKED = "blocked"

    RECOVERED = "recovered"

    FALLBACK = "fallback"


# ==========================================================
# Reputation Sources
# ==========================================================

class ReputationSource(str, Enum):
    IP = "ip"

    IDENTITY = "identity"

    FINGERPRINT = "fingerprint"


# ==========================================================
# Trust Levels
# ==========================================================

class TrustLevel(str, Enum):
    VERY_LOW = "very_low"

    LOW = "low"

    MEDIUM = "medium"

    HIGH = "high"

    VERY_HIGH = "very_high"


# ==========================================================
# Adaptive Threshold Categories
# ==========================================================

class ThresholdType(str, Enum):
    ALLOW = "allow"

    THROTTLE = "throttle"

    BLOCK = "block"


# ==========================================================
# Redis Repository Interface
# ==========================================================

class RedisRepositoryProtocol(Protocol):

    async def load_context(self, identity):
        ...

    async def persist(self, decision):
        ...


# ==========================================================
# Trust Details
# ==========================================================

class TrustBreakdown(TypedDict):
    reputation: float
    behavior: float
    recovery: float
    violations: float
    final: float


# ==========================================================
# Metadata returned to middleware/dashboard
# ==========================================================

class DecisionMetadata(TypedDict):
    adjusted_risk: float
    trust_score: float
    reputation: float
    recovery_score: float