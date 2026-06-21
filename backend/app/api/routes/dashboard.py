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
from app.client import service as client_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    last_minute = now - timedelta(minutes=1)
    prev_minute_start = last_minute - timedelta(minutes=1)
    last_15m = now - timedelta(minutes=15)
    last_60m = now - timedelta(minutes=60)
    prev_15_start = last_60m
    prev_15_end = last_60m + timedelta(minutes=15)

    high_th, med_th = get_adaptive_thresholds()

    # ── 1 query: RPS (current) + RPS (previous minute) in one pass ──────────
    rps_result = await db.execute(
        select(
            func.sum(case((RequestLog.created_at >= last_minute, 1), else_=0)).label("current"),
            func.sum(case((
                and_(RequestLog.created_at >= prev_minute_start,
                     RequestLog.created_at < last_minute), 1), else_=0
            )).label("previous"),
        )
        .where(RequestLog.created_at >= prev_minute_start)
    )
    rps_row = rps_result.one()
    requests_last_minute = rps_row.current or 0
    prev_requests = rps_row.previous or 0

    requests_per_second = round(requests_last_minute / 60, 1)
    prev_rps = prev_requests / 60
    rps_trend = round(((requests_per_second - prev_rps) / (prev_rps + 0.01)) * 100, 1)

    # ── 1 query: current + previous violations + risk composition ───────────
    # FIXED: violations now count MEDIUM + HIGH risk (risk_score > med_th)
    dec_result = await db.execute(
        select(
            # Current violations (last 15m, medium + high risk)
            func.sum(case((
                and_(DecisionLog.created_at >= last_15m,
                     DecisionLog.risk_score > med_th), 1), else_=0
            )).label("violations"),
            # Previous violations (15m window starting 60m ago, medium + high risk)
            func.sum(case((
                and_(DecisionLog.created_at >= prev_15_start,
                     DecisionLog.created_at < prev_15_end,
                     DecisionLog.risk_score > med_th), 1), else_=0
            )).label("prev_violations"),
            # Risk composition buckets (last 15m)
            func.sum(case((
                and_(DecisionLog.created_at >= last_15m,
                     DecisionLog.risk_score > high_th), 1), else_=0
            )).label("high_count"),
            func.sum(case((
                and_(DecisionLog.created_at >= last_15m,
                     DecisionLog.risk_score > med_th,
                     DecisionLog.risk_score <= high_th), 1), else_=0
            )).label("medium_count"),
            func.sum(case((
                and_(DecisionLog.created_at >= last_15m,
                     DecisionLog.risk_score <= med_th), 1), else_=0
            )).label("low_count"),
        )
        .where(DecisionLog.created_at >= prev_15_start)  # widest window drives the scan
    )
    dec_row = dec_result.one()

    violations = dec_row.violations or 0
    prev_violations = dec_row.prev_violations or 0
    high_count = dec_row.high_count or 0
    medium_count = dec_row.medium_count or 0
    low_count = dec_row.low_count or 0

    if prev_violations > 0:
        violations_trend = int(((violations - prev_violations) / prev_violations) * 100)
    else:
        violations_trend = violations * 100 if violations > 0 else 0

    total = high_count + medium_count + low_count
    traffic_composition = {
        "normal":    round((low_count    / total) * 100) if total else 0,
        "suspicious": round((medium_count / total) * 100) if total else 0,
        "high_risk": round((high_count   / total) * 100) if total else 0,
    }

    # ── 1 query: suspicious sessions (distinct user_ids with medium+ risk) ───
    sess_result = await db.execute(
        select(func.count(func.distinct(RequestLog.user_id)))
        .select_from(DecisionLog)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > med_th,
            RequestLog.user_id.isnot(None)  # Ensure we have user_id
        ))
    )
    suspicious_sessions = sess_result.scalar() or 0

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
    """
    Uses DB-side date_trunc bucketing instead of Python-side looping over a
    full result set, which avoids O(rows × buckets) work in the application.
    """
    now = datetime.utcnow()
    high_th, _ = get_adaptive_thresholds()

    if timeframe == "15m":
        trunc_unit = "minute"
        points = 15
        start_time = now - timedelta(minutes=15)
        interval_minutes = 1
    elif timeframe == "1h":
        # 5-minute buckets for 1 hour = 12 points
        trunc_unit = "minute"
        points = 12
        start_time = now - timedelta(hours=1)
        interval_minutes = 5
    else:  # 24h
        trunc_unit = "hour"
        points = 24
        start_time = now - timedelta(hours=24)
        interval_minutes = 60

    # ── Single query per table: DB aggregates, not Python ───────────────────
    request_rows = (await db.execute(
        select(
            func.date_trunc(trunc_unit, RequestLog.created_at).label("bucket"),
            func.count().label("cnt")
        )
        .where(RequestLog.created_at >= start_time)
        .group_by("bucket")
        .order_by("bucket")
    )).all()

    decision_rows = (await db.execute(
        select(
            func.date_trunc(trunc_unit, DecisionLog.created_at).label("bucket"),
            func.count().label("cnt")
        )
        .where(and_(
            DecisionLog.created_at >= start_time,
            DecisionLog.risk_score > high_th
        ))
        .group_by("bucket")
        .order_by("bucket")
    )).all()

    req_by_bucket = {row.bucket: row.cnt for row in request_rows}
    anom_by_bucket = {row.bucket: row.cnt for row in decision_rows}

    # For 1h timeframe, re-bucket minute-level rows into 5-minute slots in Python
    data_points = []
    for i in range(points):
        bucket_start = start_time + timedelta(minutes=interval_minutes * i)
        bucket_end = bucket_start + timedelta(minutes=interval_minutes)

        if timeframe == "1h":
            # Aggregate minute-level buckets into 5-min slots
            requests = sum(
                v for k, v in req_by_bucket.items()
                if bucket_start <= k < bucket_end
            )
            anomalies = sum(
                v for k, v in anom_by_bucket.items()
                if bucket_start <= k < bucket_end
            )
        else:
            # Direct lookup — one entry per bucket
            requests = req_by_bucket.get(bucket_start, 0)
            anomalies = anom_by_bucket.get(bucket_start, 0)

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
    """
    Returns users with suspicious activity (medium+ risk scores) in the last 15 minutes.
    """
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    high_th, med_th = get_adaptive_thresholds()

    # Simple query - use MIN or MAX to get any IP (PostgreSQL compatible)
    result = await db.execute(
        select(
            RequestLog.user_id.label("user_id"),
            func.min(RequestLog.ip_address).label("ip"),  # or func.max()
            func.max(DecisionLog.risk_score).label("max_risk"),
            func.max(DecisionLog.created_at).label("last_seen"),
            func.max(DecisionLog.explanation).label("reason"),
            func.max(DecisionLog.action).label("latest_action"),
            func.count(DecisionLog.id).label("violations"),
        )
        .select_from(DecisionLog)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > med_th,
            RequestLog.user_id.isnot(None),
        ))
        .group_by(RequestLog.user_id)
        .having(func.max(DecisionLog.risk_score) > med_th)
        .order_by(func.max(DecisionLog.risk_score).desc())
        .limit(limit)
    )

    suspicious_users = []
    for row in result.all():
        user_id = row.user_id
        ip = row.ip or "unknown"
        risk_score = row.max_risk or 0
        last_seen = row.last_seen
        violations = row.violations or 0
        reason = row.reason
        latest_action = row.latest_action

        is_blocked = latest_action == "block"

        if risk_score > high_th + 0.1:
            status = "critical"
        elif risk_score > high_th:
            status = "high_risk"
        elif risk_score > med_th:
            status = "elevated"
        else:
            status = "low"

        suspicious_users.append(SuspiciousUserResponse(
            id=str(user_id),
            user_id=user_id,
            violations=violations,
            threat_score=round(risk_score, 2),
            status=status,
            ip=ip,
            last_seen=last_seen,
            reason=reason or "No reason",
            is_blocked=is_blocked,
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
        risk_score = row[2]

        if risk_score > high_th + 0.1:
            alert_type = "Critical Threat"
        elif action == "block":
            alert_type = "Blocked Threat"
        elif action == "throttle":
            alert_type = "Rate Limited Threat"
        else:
            alert_type = "High Risk Activity"

        alerts.append(AlertResponse(
            id=idx + 1,
            ip=row[1] or "unknown",
            score=round(risk_score, 2),
            type=alert_type,
            timestamp=row[5],
            user_id=str(row[6]) if row[6] else None,
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
            ip_address=row[4] or "unknown",
            action=row[5],
            risk_score=round(risk_score, 2),
            explanation={
                "summary": row[8] or row[7] or "No explanation",
                "details": {
                    **(row[9] or {}),
                    "risk_level": risk_level,
                },
            },
            created_at=row[10],
        ))

    return logs


@router.get("/user/{user_id}", response_model=dict)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    high_th, med_th = get_adaptive_thresholds()

    # ── 1 query: total requests ──────────────────────────────────────────────
    total_result = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.user_id == user_id)
    )
    total_requests = total_result.scalar() or 0

    # ── FIXED: 1 query for violations (medium+ high), MAX risk, AVG risk ─────
    # Now uses med_th instead of hardcoded 0.6
    risk_result = await db.execute(
        select(
            func.sum(case((DecisionLog.risk_score > med_th, 1), else_=0)).label("violations"),
            func.max(DecisionLog.risk_score).label("max_risk"),
            func.avg(DecisionLog.risk_score).label("avg_risk"),
        )
        .where(and_(
            DecisionLog.user_id == user_id,
            DecisionLog.created_at >= last_15m,
        ))
    )
    risk_row = risk_result.one()
    
    violations = risk_row.violations or 0
    current_risk = risk_row.max_risk or 0  # MAX risk for current display
    avg_risk = risk_row.avg_risk or 0      # AVG risk for trend analysis

    # ── 1 query: recent actions ──────────────────────────────────────────────
    actions_result = await db.execute(
        select(DecisionLog.action, DecisionLog.created_at,
               DecisionLog.reason, DecisionLog.risk_score)
        .where(DecisionLog.user_id == user_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(10)
    )
    recent_actions = [
        {"action": row[0], "timestamp": row[1], "reason": row[2], "risk_score": row[3]}
        for row in actions_result.all()
    ]

    # ── 1 query: IP history (distinct IPs used by this user) ─────────────────
    ip_result = await db.execute(
        select(RequestLog.ip_address)
        .where(RequestLog.user_id == user_id)
        .distinct()
        .limit(10)
    )
    ip_history = [row[0] for row in ip_result.all() if row[0]]

    # ── Redis: block state ───────────────────────────────────────────────────
    is_blocked = await StateManager.is_blocked(user_id)

    return {
        "user_id": user_id,
        "is_anonymous": user_id > 2 ** 60,  # Your anonymous ID range
        "total_requests": total_requests,
        "violations": violations,  # Now counts medium + high risk consistently
        "current_risk_score": round(current_risk, 2),  # MAX risk in last 15 min
        "avg_risk_score": round(avg_risk, 2),  # AVG risk for trend
        "is_blocked": is_blocked,
        "recent_actions": recent_actions,
        "ip_history": ip_history,
    }


@router.get("/ip/{ip}/trend")
async def get_ip_trend(ip: str, db: AsyncSession = Depends(get_db)):
    last_1h = datetime.utcnow() - timedelta(hours=1)

    result = await db.execute(
        select(DecisionLog.created_at, DecisionLog.risk_score)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            RequestLog.ip_address == ip,
            DecisionLog.created_at >= last_1h,
        ))
        .order_by(DecisionLog.created_at)
    )

    return [{"time": row[0], "risk": row[1]} for row in result.all()]


@router.post("/user/{user_id}/block")
async def block_user(
    user_id: int,
    duration: int = Query(3600, description="Block duration in seconds"),
    db: AsyncSession = Depends(get_db)
):
    """Block a user for the specified duration."""
    try:
        await StateManager.block_user(user_id, duration)
        logger.info(f"User {user_id} blocked for {duration} seconds")
        return {
            "success": True,
            "message": f"User {user_id} blocked for {duration} seconds",
            "user_id": user_id,
            "duration": duration,
        }
    except Exception as e:
        logger.error(f"Failed to block user {user_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/user/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Unblock a user."""
    try:
        await StateManager.delete(f"user:{user_id}:blocked")
        logger.info(f"User {user_id} unblocked")
        return {
            "success": True,
            "message": f"User {user_id} unblocked",
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"Failed to unblock user {user_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/user/{user_id}/warning")
async def send_warning(
    user_id: int,
    message: str = Query(
        "Suspicious activity detected on your account",
        description="Warning message"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Send a warning to a user (logs the warning)."""
    try:
        warning_log = WarningLog(
            user_id=user_id,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.add(warning_log)
        await db.commit()
        logger.info(f"Warning sent to user {user_id}")
        return {
            "success": True,
            "message": f"Warning sent to user {user_id}",
            "user_id": user_id,
            "warning_message": message,
        }
    except Exception as e:
        logger.error(f"Failed to send warning to user {user_id}: {e}")
        return {"success": False, "error": str(e)}

