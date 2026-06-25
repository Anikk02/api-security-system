import json
import time
from typing import List

from app.activity.schemas import (
    ActivityResponse,
    ThreatEvent,
    DecisionTrendPoint,
    EndpointActivity,
    ActivityInsights,
    ActivityMetrics,
    PeakAttack,
    AttackPattern,
    SpikeCorrelation,
)

from app.activity.analyzer import (
    compute_risk,
    compute_severity,
    detect_spike_correlations,
)

from app.state.redis_client import redis_client


class ActivityService:

    @staticmethod
    async def get_activity(client_id: int, time_window: int = 600) -> ActivityResponse:
        """
        Fetch activity data optimized for time-window-based dashboard
        """

        # ============================================================
        # 🔹 KEYS
        # ============================================================
        stats_key = f"client:{client_id}:stats"
        events_key = f"client:{client_id}:events"
        endpoints_key = f"client:{client_id}:endpoints"
        trend_key = f"client:{client_id}:trend"

        # Window-based key
        current_window = int(time.time() / time_window) * time_window
        window_key = f"{stats_key}:window:{current_window}"

        # ============================================================
        # 🔥 PIPELINE (single Redis round trip)
        # ============================================================
        pipe = redis_client.pipeline()

        pipe.hgetall(stats_key)
        pipe.hgetall(window_key)
        pipe.lrange(events_key, 0, 20)
        pipe.zrevrange(endpoints_key, 0, 10, withscores=True)
        pipe.lrange(trend_key, 0, 20)
        pipe.get(f"{stats_key}:peak_time")
        pipe.get(f"{stats_key}:peak_endpoint")
        pipe.get(f"{stats_key}:peak_blocked")

        try:
            (
                stats,
                window_stats,
                raw_events,
                endpoint_data,
                raw_trend,
                peak_time_raw,
                peak_endpoint_raw,
                peak_blocked_raw,
            ) = await pipe.execute()
        except Exception:
            stats, window_stats, raw_events, endpoint_data, raw_trend = {}, {}, [], [], []
            peak_time_raw, peak_endpoint_raw, peak_blocked_raw = None, None, None

        # ============================================================
        # 🔹 CORE STATS
        # ============================================================
        source = window_stats if window_stats else stats

        allowed = int(source.get("allowed", 0))
        blocked = int(source.get("blocked", 0))
        total = int(source.get("total", 0))

        # ============================================================
        # 🔹 INSIGHTS
        # ============================================================
        risk_level, risk_percent = compute_risk(blocked, total)

        attack_status = (
            "under_attack" if blocked > allowed and blocked > 50 else "stable"
        )

        insights = ActivityInsights(
            attackStatus=attack_status,
            anomalyScore=round(risk_percent, 2),
            riskLevel=risk_level,
        )

        # ============================================================
        # 🔹 METRICS
        # ============================================================
        success_rate = (allowed / total * 100) if total else 100.0

        metrics = ActivityMetrics(
            totalRequests=total,
            blockedRequests=blocked,
            throttledRequests=0,
            successRate=round(success_rate, 2),
        )

        # 🔥 Health Score (frontend should NOT compute)
        health_score = round(success_rate, 2)

        # ============================================================
        # 🔹 PEAK ATTACK
        # ============================================================
        def decode(val):
            return val.decode() if isinstance(val, bytes) else val

        peak_time = decode(peak_time_raw)
        peak_endpoint = decode(peak_endpoint_raw)

        try:
            peak_blocked = int(peak_blocked_raw) if peak_blocked_raw else blocked
        except:
            peak_blocked = blocked

        peak = PeakAttack(
            time=peak_time,
            blocked=peak_blocked,
            endpoint=peak_endpoint,
            severity=compute_severity(peak_blocked),
        )

        # ============================================================
        # 🔹 TIMELINE
        # ============================================================
        timeline: List[ThreatEvent] = []

        for e in raw_events or []:
            try:
                val = e.decode() if isinstance(e, bytes) else e
                data = json.loads(val)
                timeline.append(ThreatEvent(**data))
            except Exception:
                continue

        # ============================================================
        # 🔹 ENDPOINTS + PATTERNS + TOP ENDPOINT
        # ============================================================
        endpoints: List[EndpointActivity] = []
        patterns: List[AttackPattern] = []

        top_endpoint_data = None

        for i, (ep, count) in enumerate(endpoint_data or []):
            ep = ep.decode() if isinstance(ep, bytes) else ep
            count = int(count)

            percentage = (count / total * 100) if total else 0
            risk, _ = compute_risk(count, total)

            # 🔥 Estimate blocked proportionally
            blocked_estimate = int((blocked / total) * count) if total else 0

            endpoint_obj = EndpointActivity(
                endpoint=ep,
                percentage=round(percentage, 2),
                requests=count,
                blocked=blocked_estimate,
                risk=risk,
            )

            endpoints.append(endpoint_obj)

            patterns.append(
                AttackPattern(
                    endpoint=ep,
                    percentage=round(percentage, 2),
                )
            )

            # 🔥 Top Endpoint
            if i == 0:
                top_endpoint_data = {
                    "endpoint": ep,
                    "requests": count,
                    "percentage": round(percentage, 2),
                }

        # ============================================================
        # 🔹 TREND
        # ============================================================
        trend: List[DecisionTrendPoint] = []

        for t in raw_trend or []:
            try:
                val = t.decode() if isinstance(t, bytes) else t
                data = json.loads(val)
                trend.append(DecisionTrendPoint(**data))
            except Exception:
                continue

        # ============================================================
        # 🔹 SPIKE CORRELATIONS
        # ============================================================
        correlations = await detect_spike_correlations(client_id, time_window)

        if not correlations and peak_time and peak_endpoint:
            correlations.append(
                SpikeCorrelation(
                    peak_time=peak_time,
                    blocked=peak_blocked,
                    target=peak_endpoint,
                )
            )

        # ============================================================
        # 🔹 FINAL RESPONSE
        # ============================================================
        return ActivityResponse(
            timeline=timeline,
            endpoints=endpoints,
            trend=trend,
            insights=insights,
            metrics=metrics,
            peak=peak,
            patterns=patterns,
            correlations=correlations,
            topEndpoint=top_endpoint_data,
            healthScore=health_score,
        )