# app/policy/policy_engine.py

from __future__ import annotations

from .adaptive_thresholds import adaptive_thresholds
from .constants import (
    BLOCK_DURATIONS,
    THROTTLE_DURATION,
)
from .context import PenaltyContext
from .decision import PenaltyDecision
from .types import Action


class PolicyEngine:
    """
    Pure business decision engine.

    Inputs
    ------
    - PenaltyContext
    - trust score (0-1)

    Outputs
    -------
    PenaltyDecision

    This class NEVER talks to Redis.
    """

    # ---------------------------------------------------------

    @classmethod
    def evaluate(
        cls,
        context: PenaltyContext,
        trust_score: float,
    ) -> PenaltyDecision:

        # trust_score is 1.0 = fully trustworthy, 0.0 = fully
        # suspicious (see TrustEngine). The adaptive thresholds
        # are percentile-based over the "worst" tail of traffic,
        # so we feed them a suspicion score (inverse of trust)
        # rather than trust_score itself.
        suspicion_score = 1.0 - trust_score

        adaptive_thresholds.update(
            context.client_id,
            suspicion_score,
        )

        high_threshold, medium_threshold = (
            adaptive_thresholds.thresholds(
                context.client_id
            )
        )

        # -------------------------------------------------
        # Already blocked
        # -------------------------------------------------

        if context.is_blocked:
            return cls._block(
                context,
                trust_score,
                "Identity already blocked",
                "hard",
            )

        if context.ip_blocked:
            return cls._block(
                context,
                trust_score,
                "IP already blocked",
                "hard",
            )

        if context.fingerprint_blocked:
            return cls._block(
                context,
                trust_score,
                "Fingerprint already blocked",
                "hard",
            )

        # -------------------------------------------------
        # Active throttle
        # -------------------------------------------------

        if context.is_throttled:

            return PenaltyDecision(
                action="throttle",
                reason="Throttle already active",

                risk_score=context.risk_score,
                trust_score=trust_score,
                reputation=context.combined_reputation,

                should_throttle=True,
                throttle_duration=THROTTLE_DURATION,
            )

        # -------------------------------------------------
        # Hard IP rotation
        # -------------------------------------------------

        if (
            context.unique_ip_count >= 5
            and suspicion_score >= medium_threshold
        ):
            return cls._block(
                context,
                trust_score,
                f"{context.unique_ip_count} IPs used within 5 minutes",
                "hard",
            )

        # -------------------------------------------------
        # Medium IP rotation
        # -------------------------------------------------

        if (
            context.unique_ip_count >= 3
            and suspicion_score >= medium_threshold
        ):

            return PenaltyDecision(
                action="throttle",
                reason="Suspicious IP rotation",

                risk_score=context.risk_score,
                trust_score=trust_score,
                reputation=context.combined_reputation,

                reputation_delta=0.03,
                should_throttle=True,
                throttle_duration=THROTTLE_DURATION,

                metadata={
                    "unique_ips": context.unique_ip_count,
                },
            )

        # -------------------------------------------------
        # High suspicion score
        # -------------------------------------------------

        if suspicion_score >= high_threshold:

            severity = (
                "hard"
                if context.violation_count >= 6
                else "medium"
            )

            return cls._block(
                context,
                trust_score,
                "High suspicion score",
                severity,
            )

        # -------------------------------------------------
        # Medium suspicion score
        # -------------------------------------------------

        if suspicion_score >= medium_threshold:

            return PenaltyDecision(
                action="throttle",
                reason="Elevated suspicion score",

                risk_score=context.risk_score,
                trust_score=trust_score,
                reputation=context.combined_reputation,

                reputation_delta=0.02,

                should_throttle=True,
                throttle_duration=THROTTLE_DURATION,

                increment_violation=True,

                metadata={
                    "threshold": medium_threshold,
                },
            )

        # -------------------------------------------------
        # Normal traffic
        # -------------------------------------------------

        return PenaltyDecision(
            action="allow",
            reason="Normal traffic",

            risk_score=context.risk_score,
            trust_score=trust_score,
            reputation=context.combined_reputation,

            metadata={
                "threshold": medium_threshold,
            },
        )

    # ---------------------------------------------------------

    @staticmethod
    def _block(
        context: PenaltyContext,
        trust_score: float,
        reason: str,
        severity: str,
    ) -> PenaltyDecision:

        duration = BLOCK_DURATIONS[severity]

        return PenaltyDecision(
            action="block",
            reason=reason,

            risk_score=context.risk_score,
            trust_score=trust_score,
            reputation=context.combined_reputation,

            reputation_delta=0.08,

            should_block=True,
            block_severity=severity,
            block_duration=duration,

            increment_violation=True,

            metadata={
                "severity": severity,
            },
        )