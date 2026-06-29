from __future__ import annotations

from dataclasses import dataclass

from app.policy.constants import (
    EWMA_ALPHA,
    HIGH_PERCENTILE,
    MEDIUM_PERCENTILE,
    MIN_HIGH_THRESHOLD,
    MAX_HIGH_THRESHOLD,
    MIN_MEDIUM_THRESHOLD,
    MAX_MEDIUM_THRESHOLD,
    DEFAULT_HIGH_THRESHOLD,
    DEFAULT_MEDIUM_THRESHOLD,
    THRESHOLD_HISTORY,
)


@dataclass(slots=True)
class AdaptiveThresholds:
    high: float
    medium: float


class AdaptiveThresholdEngine:
    """
    Computes adaptive thresholds from historical risk scores.

    RedisRepository supplies:

        history = [
            0.12,
            0.18,
            0.22,
            ...
        ]

    Repository is responsible for storing the history.

    This class only computes thresholds.
    """

    def __init__(self) -> None:
        # Per-client rolling history + cached thresholds.
        # In-memory only: a single process's view. Fine for a
        # single-instance deployment; a multi-instance deployment
        # would need this backed by Redis instead.
        self._history: dict[int | None, list[float]] = {}
        self._cache: dict[int | None, AdaptiveThresholds] = {}

    def update(self, client_id: int | None, value: float) -> None:
        """
        Record a new observation (e.g. a suspicion score) for
        this client and recompute its cached thresholds.
        """

        history = self._history.setdefault(client_id, [])

        history.append(value)

        if len(history) > THRESHOLD_HISTORY:
            del history[: len(history) - THRESHOLD_HISTORY]

        previous = self._cache.get(client_id)

        self._cache[client_id] = self.compute(
            history,
            previous_high=previous.high if previous else None,
            previous_medium=previous.medium if previous else None,
        )

    def thresholds(
        self,
        client_id: int | None,
    ) -> tuple[float, float]:
        """
        Return the cached (high, medium) thresholds for this
        client, falling back to defaults if nothing has been
        recorded yet.
        """

        cached = self._cache.get(client_id)

        if cached is None:
            return (
                DEFAULT_HIGH_THRESHOLD,
                DEFAULT_MEDIUM_THRESHOLD,
            )

        return cached.high, cached.medium

    def compute(
        self,
        history: list[float],
        previous_high: float | None = None,
        previous_medium: float | None = None,
    ) -> AdaptiveThresholds:

        if len(history) < 30:
            return AdaptiveThresholds(
                high=0.75,
                medium=0.50,
            )

        history = sorted(history)

        high = self._percentile(history, HIGH_PERCENTILE)
        medium = self._percentile(history, MEDIUM_PERCENTILE)

        high = max(high, MIN_HIGH_THRESHOLD)
        medium = max(medium, MIN_MEDIUM_THRESHOLD)

        high = min(high, MAX_HIGH_THRESHOLD)
        medium = min(medium, MAX_MEDIUM_THRESHOLD)

        if previous_high is not None:
            high = self._ewma(previous_high, high)

        if previous_medium is not None:
            medium = self._ewma(previous_medium, medium)

        return AdaptiveThresholds(
            high=round(high, 4),
            medium=round(medium, 4),
        )

    @staticmethod
    def _percentile(values: list[float], p: int) -> float:

        if not values:
            return 0.0

        k = int((len(values) - 1) * p / 100)

        return values[k]

    @staticmethod
    def _ewma(old: float, new: float) -> float:
        return (1 - EWMA_ALPHA) * old + EWMA_ALPHA * new
    

adaptive_thresholds = AdaptiveThresholdEngine()