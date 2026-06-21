from collections import defaultdict

def analyze_activity(logs):
    trend_map = defaultdict(lambda: {"allowed": 0, "blocked": 0, "throttled": 0})
    endpoint_map = defaultdict(lambda: {"requests": 0, "blocked": 0})
    timeline = []

    for log in logs:
        time_key = log.created_at.strftime("%H:%M")

        trend_map[time_key][log.status] += 1

        endpoint_map[log.endpoint]["requests"] += 1
        if log.status == "blocked":
            endpoint_map[log.endpoint]["blocked"] += 1

        if log.status != "allowed":
            timeline.append({
                "time": time_key,
                "event": log.reason or "Suspicious activity",
                "description": f"{log.status} detected",
                "severity": "high" if log.status == "blocked" else "medium",
                "ip": log.ip_address
            })

    trend = [
        {"time": t, **vals}
        for t, vals in sorted(trend_map.items())
    ]

    total = sum(sum(v.values()) for v in trend_map.values())

    endpoints = []
    for ep, vals in endpoint_map.items():
        percentage = (vals["requests"] / total * 100) if total else 0

        endpoints.append({
            "endpoint": ep,
            "percentage": round(percentage, 2),
            "requests": vals["requests"],
            "blocked": vals["blocked"],
            "risk": "high" if vals["blocked"] > 50 else "low"
        })

    peak = max(trend, key=lambda x: x["blocked"], default=None)

    return {
        "timeline": timeline[-20:],
        "endpoints": endpoints,
        "trend": trend,

        "insights": {
            "attackStatus": "HIGH" if peak and peak["blocked"] > 50 else "LOW",
            "anomalyScore": 0.8,
            "riskLevel": "HIGH"
        },

        "metrics": {
            "totalRequests": total,
            "blockedRequests": sum(t["blocked"] for t in trend),
            "throttledRequests": sum(t["throttled"] for t in trend),
            "successRate": 75
        },

        "peak": {
            "time": peak["time"] if peak else None,
            "blocked": peak["blocked"] if peak else 0,
            "endpoint": None
        },

        "patterns": [],
        "correlations": []
    }