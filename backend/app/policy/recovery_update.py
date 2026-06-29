from dataclasses import dataclass


@dataclass(slots=True)
class RecoveryUpdate:
    """
    State updates to apply after the policy decision.

    Pure data.
    No Redis.
    """

    reputation_delta: float = 0.0

    trust_delta: float = 0.0

    violation_delta: int = 0

    clear_throttle: bool = False

    clear_block: bool = False

    decay_reputation: bool = False