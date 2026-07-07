from __future__ import annotations

from dataclasses import dataclass

from app.policy.context import PenaltyContext
from app.policy.decision import PenaltyDecision


@dataclass(slots=True)
class RecoveryResult:
    """
    Result produced by RecoveryEngine.

    reputation_delta:
        Amount to add to reputation score.
        Positive -> reputation worsens.
        Negative -> reputation improves.

    recovery_bonus:
        Bonus trust that can be applied on future requests.

    reset_throttle:
        Whether throttle state should be cleared.
    """

    reputation_delta: float
    recovery_bonus: float
    reset_throttle: bool


class RecoveryEngine:
    """
    Computes recovery and reputation updates.

    Responsibilities
    ----------------
    • Decides how reputation changes.
    • Computes recovery bonus.
    • Never accesses Redis.
    • Never blocks users.
    • Never throttles users.
    """

    def evaluate(
        self,
        ctx: PenaltyContext,
        decision: PenaltyDecision,
    ) -> RecoveryResult:

        reputation_delta = 0.0
        recovery_bonus = 0.0
        reset_throttle = False

        # -------------------------------------------------
        # BLOCK
        # -------------------------------------------------

        if decision.action == "block":

            reputation_delta = 0.20

        # -------------------------------------------------
        # THROTTLE
        # -------------------------------------------------

        elif decision.action == "throttle":

            reputation_delta = 0.05

        # -------------------------------------------------
        # ALLOW
        # -------------------------------------------------

        else:

            # Low-risk traffic slowly rebuilds reputation.

            if (
                ctx.risk_score < 0.30
                and ctx.error_count == 0
                and ctx.request_count < 20
            ):

                reputation_delta = -0.02
                recovery_bonus = 0.05

            elif ctx.risk_score < 0.50:

                reputation_delta = -0.01
                recovery_bonus = 0.02

            # If previously throttled and now behaving well,
            # throttle can safely be removed.

            if (
                ctx.is_throttled
                and ctx.risk_score < 0.40
            ):
                reset_throttle = True

        return RecoveryResult(
            reputation_delta=round(reputation_delta, 4),
            recovery_bonus=round(recovery_bonus, 4),
            reset_throttle=reset_throttle,
        )

    # ---------------------------------------------------------

    @classmethod
    def apply(
        cls,
        *,
        context: PenaltyContext,
        decision: PenaltyDecision,
    ) -> PenaltyDecision:
        """
        Convenience wrapper used by PenaltyManager.

        Runs evaluate() and merges the resulting RecoveryResult
        onto the decision produced by PolicyEngine, since
        RecoveryEngine itself never mutates decisions
        (see class docstring).
        """

        result = cls().evaluate(context, decision)

        decision.recovery_delta = result.reputation_delta
        decision.should_recover = (
            result.reputation_delta != 0.0
            or result.recovery_bonus != 0.0
        )

        decision.metadata["recovery_bonus"] = result.recovery_bonus

        if result.reset_throttle and decision.should_throttle:
            decision.should_throttle = False
            decision.throttle_duration = 0

            if decision.action == "throttle":
                decision.action = "allow"
                decision.reason = (
                    "Recovered - throttle reset"
                )

        return decision