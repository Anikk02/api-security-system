import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.api.deps import get_db
from app.schemas.dashboard import (
    DashboardStatsResponse,
    TrafficResponse,
    TrafficDataPoint,
    SuspiciousUserResponse,
    AlertResponse,
    LogResponse
)
from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog
from app.db.models.warning_log import WarningLog
from app.risk.risk_engine import get_adaptive_thresholds
from app.state.state_manager import StateManager
from app.state.redis_client import redis_client
from app.policy.penalty_manager import BLOCK_DURATIONS

from app.authentication.dependencies import require_active_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_active_client)]
)

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):

    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    last_60m = now - timedelta(minutes=60)

    high_th, med_th = get_adaptive_thresholds()

    # --- RPS ---
    last_minute = now - timedelta(minutes=1)
    result = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.created_at >= last_minute)
    )
    requests_last_minute = result.scalar() or 0
    requests_per_second = round(requests_last_minute / 60, 1)

    # --- Violations (HIGH RISK ONLY) ---
    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(
            and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score > high_th
            )
        )
    )
    violations = result.scalar() or 0

    # --- Previous violations ---
    prev_15_start = last_60m
    prev_15_end = last_60m + timedelta(minutes=15)

    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(
            and_(
                DecisionLog.created_at >= prev_15_start,
                DecisionLog.created_at < prev_15_end,
                DecisionLog.risk_score > high_th
            )
        )
    )
    prev_violations = result.scalar() or 0

    if prev_violations > 0:
        violations_trend = int(((violations - prev_violations) / prev_violations) * 100)
    else:
        violations_trend = violations * 100 if violations > 0 else 0

    # --- Suspicious sessions (MEDIUM+) ---
    result = await db.execute(
        select(func.count(func.distinct(RequestLog.ip_address)))
        .select_from(DecisionLog)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > med_th
        ))
    )
    suspicious_sessions = result.scalar() or 0

    # --- Traffic Composition ---
    risk_case = case(
        (DecisionLog.risk_score > high_th, "high"),
        (DecisionLog.risk_score > med_th, "medium"),
        else_="low"
    )

    result = await db.execute(
        select(risk_case.label("risk_level"), func.count())
        .where(DecisionLog.created_at >= last_15m)
        .group_by("risk_level")
    )

    risk_counts = {row[0]: row[1] for row in result.all()}
    total = sum(risk_counts.values())

    traffic_composition = {
        "normal": round((risk_counts.get('low', 0) / total) * 100) if total else 0,
        "suspicious": round((risk_counts.get('medium', 0) / total) * 100) if total else 0,
        "high_risk": round((risk_counts.get('high', 0) / total) * 100) if total else 0
    }

    # --- RPS Trend ---
    prev_minute_start = last_minute - timedelta(minutes=1)
    prev_minute_end = last_minute

    result = await db.execute(
        select(func.count(RequestLog.id))
        .where(and_(
            RequestLog.created_at >= prev_minute_start,
            RequestLog.created_at < prev_minute_end
        ))
    )

    prev_rps = (result.scalar() or 0) / 60
    rps_trend = round(((requests_per_second - prev_rps) / (prev_rps + 0.01)) * 100, 1)

    return DashboardStatsResponse(
        requests_per_second=requests_per_second,
        requests_trend=rps_trend,
        violations_detected=violations,
        violations_trend=violations_trend,
        suspicious_sessions=suspicious_sessions,
        sessions_trend=0,
        traffic_composition=traffic_composition
    )

@router.get("/traffic", response_model=TrafficResponse)
async def get_traffic_data(
    timeframe: str = Query("15m", regex="^(15m|1h|24h)$"),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    high_th, _ = get_adaptive_thresholds()

    if timeframe == "15m":
        interval = timedelta(minutes=1)
        points = 15
        start_time = now - timedelta(minutes=15)
    elif timeframe == "1h":
        interval = timedelta(minutes=15)
        points = 12
        start_time = now - timedelta(hours=1)
    else:
        interval = timedelta(hours=1)
        points = 24
        start_time = now - timedelta(hours=24)

    decision_rows = (await db.execute(
        select(DecisionLog.created_at, DecisionLog.risk_score)
        .where(DecisionLog.created_at >= start_time)
    )).all()

    request_rows = (await db.execute(
        select(RequestLog.created_at)
        .where(RequestLog.created_at >= start_time)
    )).all()

    data_points = []

    for i in range(points):
        bucket_start = start_time + (interval * i)
        bucket_end = bucket_start + interval

        requests = sum(1 for r in request_rows if bucket_start <= r[0] < bucket_end)

        anomalies = sum(
            1 for d in decision_rows
            if bucket_start <= d[0] < bucket_end and d[1] > high_th
        )

        data_points.append(TrafficDataPoint(
            time=bucket_start,
            requests=requests,
            anomalies=anomalies,
            blocked=0
        ))

    return TrafficResponse(data=data_points, timeframe=timeframe)

@router.get("/suspicious-users", response_model=List[SuspiciousUserResponse])
async def get_suspicious_users(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)

    high_th, med_th = get_adaptive_thresholds()

    subquery = (
        select(
            RequestLog.user_id.label("user_id"),
            RequestLog.ip_address.label("ip"),
            func.max(DecisionLog.risk_score).label('max_risk'),
            func.max(DecisionLog.created_at).label('last_seen'),
            func.max(DecisionLog.explanation).label('reason'),
            func.max(DecisionLog.action).label('latest_action')
        )
        .select_from(DecisionLog)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(DecisionLog.created_at >= last_15m)
        .group_by(RequestLog.user_id, RequestLog.ip_address)
        .having(func.max(DecisionLog.risk_score) > med_th)
        .subquery()
    )

    result = await db.execute(
        select(
            subquery.c.user_id,
            subquery.c.ip,
            subquery.c.max_risk,
            subquery.c.last_seen,
            func.count(func.distinct(DecisionLog.id)).label('violations'),
            subquery.c.reason,
            subquery.c.latest_action
        )
        .select_from(subquery)
        .join(RequestLog, RequestLog.ip_address == subquery.c.ip)
        .join(DecisionLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > med_th
        ))
        .group_by(subquery.c.user_id, subquery.c.ip, subquery.c.max_risk, subquery.c.last_seen, subquery.c.reason, subquery.c.latest_action)
        .order_by(subquery.c.max_risk.desc())
        .limit(limit)
    )

    suspicious_users = []

    for row in result.all():
        user_id = row.user_id
        ip = row.ip
        risk_score = row.max_risk
        last_seen = row.last_seen
        violations = row.violations
        reason = row.reason
        latest_action = row.latest_action

        is_blocked = latest_action == 'block'

        if risk_score > high_th + 0.1:
            status = 'critical'
        elif risk_score > high_th:
            status = 'high_risk'
        elif risk_score > med_th:
            status = 'elevated'
        else:
            status = 'low'

        suspicious_users.append(SuspiciousUserResponse(
            id=str(user_id) if user_id else f"ip-{ip}",
            user_id=user_id,
            violations=violations or 0,
            threat_score=round(risk_score or 0, 2),
            status=status,
            ip=ip,
            last_seen=last_seen,
            reason=reason or "No reason",
            is_blocked=is_blocked
        ))

    return suspicious_users

@router.get("/alerts", response_model=List[AlertResponse])
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)

    high_th, _ = get_adaptive_thresholds()

    result = await db.execute(
        select(
            DecisionLog.id,
            RequestLog.ip_address,
            DecisionLog.risk_score,
            DecisionLog.action,
            DecisionLog.reason,
            DecisionLog.created_at,
            DecisionLog.user_id
        )
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > high_th
        ))
        .order_by(DecisionLog.risk_score.desc())
        .limit(limit)
    )

    alerts = []

    for idx, row in enumerate(result.all()):
        action = row[3]

        # Better classification
        if row[2] > high_th + 0.1:
            alert_type = "Critical Threat"
        elif action == "block":
            alert_type = "Blocked Threat"
        elif action == "throttle":
            alert_type = "Rate Limited Threat"
        else:
            alert_type = "High Risk Activity"

        alerts.append(AlertResponse(
            id=idx + 1,
            ip=row[1] or 'unknown',
            score=round(row[2], 2),
            type=alert_type,
            timestamp=row[5],
            user_id=str(row[6]) if row[6] else None
        ))

    return alerts


@router.get("/logs", response_model=List[LogResponse])
async def get_decision_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit

    high_th, med_th = get_adaptive_thresholds()

    result = await db.execute(
        select(
            DecisionLog.id,
            DecisionLog.request_uuid,
            DecisionLog.user_id,
            RequestLog.endpoint,
            RequestLog.ip_address,
            DecisionLog.action,
            DecisionLog.risk_score,
            DecisionLog.reason,
            DecisionLog.explanation,
            DecisionLog.explanation_json,
            DecisionLog.created_at
        )
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .order_by(DecisionLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    logs = []

    for row in result.all():
        risk_score = row[6] or 0

        # Risk level classification (aligned with engine)
        if risk_score > high_th:
            risk_level = "high"
        elif risk_score > med_th:
            risk_level = "medium"
        else:
            risk_level = "low"

        logs.append(LogResponse(
            id=row[0],
            request_uuid=row[1],
            user_id=row[2],
            endpoint=row[3],
            ip_address=row[4] or 'unknown',
            action=row[5],
            risk_score=round(risk_score, 2),

            # explanation
            explanation={
                "summary": row[8] or row[7] or "No explanation",
                "details": {
                    **(row[9] or {}),
                    "risk_level": risk_level
                }
            },

            created_at=row[10]
        ))

    return logs

@router.get("/user/{user_id}", response_model=dict)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)

    # --- Total requests ---
    result = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.user_id == user_id)
    )
    total_requests = result.scalar() or 0

    # --- Risk-based violations ---
    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(and_(
            DecisionLog.user_id == user_id,
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > 0.6
        ))
    )
    violations = result.scalar() or 0

    # Use MAX risk instead of AVG for 15-min window 
    result = await db.execute(
        select(func.max(DecisionLog.risk_score))
        .where(and_(
            DecisionLog.user_id == user_id,
            DecisionLog.created_at >= last_15m
        ))
    )
    current_risk = result.scalar() or 0

    # Provide AVG risk for trend analysis
    result_avg = await db.execute(
        select(func.avg(DecisionLog.risk_score))
        .where(and_(
            DecisionLog.user_id == user_id,
            DecisionLog.created_at >= last_15m
        ))
    )
    avg_risk = result_avg.scalar() or 0

    # --- Recent actions ---
    result = await db.execute(
        select(DecisionLog.action, DecisionLog.created_at, DecisionLog.reason, DecisionLog.risk_score)
        .where(DecisionLog.user_id == user_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(10)
    )
    recent_actions = [
        {"action": row[0], "timestamp": row[1], "reason": row[2], "risk_score": row[3]}
        for row in result.all()
    ]

    # --- IP history (keep) ---
    result = await db.execute(
        select(RequestLog.ip_address)
        .where(RequestLog.user_id == user_id)
        .distinct()
        .limit(10)
    )
    ip_history = [row[0] for row in result.all() if row[0]]

    # --- Redis block state---
    is_blocked = await StateManager.is_blocked(user_id)

    return {
        "user_id": user_id,
        "is_anonymous": user_id > 2**60,
        "total_requests": total_requests,
        "violations": violations,
        "current_risk_score": round(current_risk, 2),  # Uses MAX risk
        "avg_risk_score": round(avg_risk, 2), # Uses AVG risk for trend analysis
        "is_blocked": is_blocked,
        "recent_actions": recent_actions,
        "ip_history": ip_history
    }

@router.get("/ip/{ip}/trend")
async def get_ip_trend(ip: str, db: AsyncSession = Depends(get_db)):

    last_1h = datetime.utcnow() - timedelta(hours=1)

    result = await db.execute(
        select(
            DecisionLog.created_at,
            DecisionLog.risk_score
        )
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(
            and_(
                RequestLog.ip_address == ip,
                DecisionLog.created_at >= last_1h
            )
        )
        .order_by(DecisionLog.created_at)
    )

    return [
        {"time": row[0], "risk": row[1]}
        for row in result.all()
    ]

@router.post("/user/{user_id}/block")
async def block_user(
    user_id: int,
    duration: int = Query(3600, description="Block duration in seconds"),
    db: AsyncSession = Depends(get_db)
):
    """ Block a user for specified duration"""
    try:
        await StateManager.block_user(user_id, duration)

        #Log the block action
        logger.info(f"User {user_id} blocked for {duration} seconds")

        return {
            "success": True,
            "message": f"User {user_id} blocked for {duration} seconds",
            "user_id": user_id,
            "duration": duration
        }
    except Exception as e:
        logger.error(f"Failed to block user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    
@router.post("/user/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Unblock a user"""
    try:
        #Remove block from Redis
        key = f"user:{user_id}:blocked"
        await redis_client.delete(key)

        logger.info(f"User {user_id} unblocked")

        return {
            "success": True,
            "message": f"User {user_id} unblocked",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Failed to unblock user {user_id}: {e}")
        return {"success": False, "error": str(e)}
    
@router.post("/user/{user_id}/warning")
async def send_warning(
    user_id: int,
    message: str = Query("Suspicious activity detected on your account", description="Warning message"),
    db: AsyncSession = Depends(get_db)
):
    """Send a warning to user (logs the warning)"""

    try:
        #Log warning to database
        warning_log = WarningLog(
            user_id=user_id,
            message=message,
            created_at=datetime.now()
        )
        db.add(warning_log)
        await db.commit()

        logger.info(f"Warning sent to user {user_id}")

        return {
            "success": True,
            "message": f"Warning sent to user {user_id}",
            "user_id": user_id,
            "warning_message": message
        }
    except Exception as e:
        logger.error(f"Failed to send warning to user {user_id}: {e}")
        return {"success": False, "error": str(e)}

