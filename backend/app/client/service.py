from sqlalchemy import text

# 📊 CLIENT ACTIVITY SERVICE

async def get_activity(db, client_id: int):

    # =========================
    # 1. THREAT TIMELINE
    # =========================
    timeline_result = await db.execute(text("""
        SELECT created_at, event_type, message, severity
        FROM warning_log
        WHERE client_id = :client_id
        ORDER BY created_at DESC
        LIMIT 20
    """), {"client_id": client_id})

    threat_timeline = [
        {
            "time": str(row[0]),
            "event": row[1],
            "description": row[2],
            "severity": row[3],
        }
        for row in timeline_result.fetchall()
    ]

    # =========================
    # 2. DECISION TREND (TIME BASED)
    # =========================
    trend_result = await db.execute(text("""
        SELECT 
            DATE_TRUNC('minute', created_at) as time,
            SUM(CASE WHEN decision = 'allow' THEN 1 ELSE 0 END) as allowed,
            SUM(CASE WHEN decision = 'throttle' THEN 1 ELSE 0 END) as throttled,
            SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) as blocked
        FROM decision_log
        WHERE client_id = :client_id
        GROUP BY time
        ORDER BY time ASC
        LIMIT 30
    """), {"client_id": client_id})

    decision_trend = [
        {
            "time": str(row[0]),
            "allowed": row[1],
            "throttled": row[2],
            "blocked": row[3],
        }
        for row in trend_result.fetchall()
    ]

    # =========================
    # 3. ENDPOINT HOTSPOTS
    # =========================
    endpoint_result = await db.execute(text("""
        SELECT endpoint, COUNT(*) as count
        FROM request_log
        WHERE client_id = :client_id
        GROUP BY endpoint
        ORDER BY count DESC
        LIMIT 5
    """), {"client_id": client_id})

    rows = endpoint_result.fetchall()
    total = sum([row[1] for row in rows]) or 1

    endpoint_distribution = [
        {
            "endpoint": row[0],
            "percentage": int((row[1] / total) * 100),
        }
        for row in rows
    ]

    return {
        "threat_timeline": threat_timeline,
        "decision_trend": decision_trend,
        "endpoint_distribution": endpoint_distribution,
    }

async def get_profile(db, client_id: int):
    return {
        "id": client_id,
        "email": "test@example.com",
        "created_at": "2026-01-01"
    }


async def update_profile(db, client_id: int, email: str):
    return True