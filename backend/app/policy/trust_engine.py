from __future__ import annotations

from dataclasses import dataclass

from app.policy.context import PenaltyContext
from app.policy.types import TrustLevel


@dataclass(slots=True)
class TrustResult:
    """
    Result produced by the TrustEngine.
    """

    trust: float
    level: TrustLevel
    reasons: list[str]


class TrustEngine:
    """
    Computes the trust score of an identity.

    Responsibilities
    ----------------
    • Uses current context only.
    • Does not access Redis.
    • Does not modify state.
    • Does not make policy decisions.
    """

    # Relative importance of each signal
    RISK_WEIGHT = 0.55
    REPUTATION_WEIGHT = 0.20

    MAX_VIOLATION_PENALTY = 0.15
    MAX_REQUEST_PENALTY = 0.05
    MAX_ERROR_PENALTY = 0.05
    MAX_IP_ROTATION_PENALTY = 0.10

    def evaluate(self, ctx: PenaltyContext) -> TrustResult:

        trust = 1.0
        reasons: list[str] = []

        # -------------------------------------------------
        # Overall Risk
        # -------------------------------------------------

        risk_penalty = ctx.risk_score * self.RISK_WEIGHT
        trust -= risk_penalty

        if ctx.risk_score >= 0.85:
            reasons.append("Very high overall risk")

        elif ctx.risk_score >= 0.70:
            reasons.append("High overall risk")

        elif ctx.risk_score >= 0.50:
            reasons.append("Elevated overall risk")

        # -------------------------------------------------
        # Reputation
        # -------------------------------------------------

        reputation_penalty = (
            ctx.combined_reputation * self.REPUTATION_WEIGHT
        )

        trust -= reputation_penalty

        if ctx.combined_reputation >= 0.80:
            reasons.append("Poor reputation")

        elif ctx.combined_reputation >= 0.60:
            reasons.append("Reputation under observation")

        # -------------------------------------------------
        # Violations
        # -------------------------------------------------

        violation_penalty = min(
            ctx.violation_count * 0.015,
            self.MAX_VIOLATION_PENALTY,
        )

        trust -= violation_penalty

        if ctx.violation_count >= 5:
            reasons.append(
                f"{ctx.violation_count} recent violations"
            )

        # -------------------------------------------------
        # Request Volume
        # -------------------------------------------------

        if ctx.request_count > 40:

            request_penalty = min(
                (ctx.request_count - 40) / 200,
                self.MAX_REQUEST_PENALTY,
            )

            trust -= request_penalty

            reasons.append(
                f"High request volume ({ctx.request_count}/min)"
            )

        # -------------------------------------------------
        # Error Count
        # -------------------------------------------------

        if ctx.error_count > 10:

            error_penalty = min(
                ctx.error_count / 300,
                self.MAX_ERROR_PENALTY,
            )

            trust -= error_penalty

            reasons.append(
                f"{ctx.error_count} recent errors"
            )

        # -------------------------------------------------
        # IP Rotation
        # -------------------------------------------------

        if ctx.unique_ip_count > 1:

            rotation_penalty = min(
                ctx.unique_ip_count * 0.02,
                self.MAX_IP_ROTATION_PENALTY,
            )

            trust -= rotation_penalty

            reasons.append(
                f"{ctx.unique_ip_count} different IPs observed"
            )

        # -------------------------------------------------
        # Recovery Bonus
        # -------------------------------------------------

        if ctx.recovery_score > 0:

            trust += ctx.recovery_score

            reasons.append("Recovered from previous suspicious activity")

        # -------------------------------------------------
        # Clamp
        # -------------------------------------------------

        trust = max(0.0, min(trust, 1.0))

        # -------------------------------------------------
        # Trust Level
        # -------------------------------------------------

        if trust >= 0.80:
            level = TrustLevel.HIGH

        elif trust >= 0.50:
            level = TrustLevel.MEDIUM

        else:
            level = TrustLevel.LOW

        return TrustResult(
            trust=round(trust, 4),
            level=level,
            reasons=reasons,
        )

    # ---------------------------------------------------------

    @classmethod
    def compute(cls, ctx: PenaltyContext) -> float:
        """
        Convenience wrapper used by PenaltyManager.

        Runs evaluate() and returns just the trust score,
        stashing the human-readable reasons on the context's
        metadata dict for explainability/logging.
        """

        result = cls().evaluate(ctx)

        ctx.metadata["trust_reasons"] = result.reasons
        ctx.metadata["trust_level"] = result.level.value

        return result.trust