import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

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
from app.db.models.ml_prediction import MLPrediction
from app.state.state_manager import StateManager
from app.state.redis_client import redis_client
from app.policy.penalty_manager import BLOCK_DURATIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # -- Get real-time dashboards statistics -- #

    #Get current time boundaries
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    last_60m = now - timedelta(minutes=60)

    #Total requests in last minute ( for RPS)
    last_minute = now - timedelta(minutes=1)
    result = await db.execute(
        select(func.count(RequestLog.id)).where(RequestLog.created_at >= last_minute)
    )
    requests_last_minute = result.scalar() or 0
    requests_per_second = round(requests_last_minute / 60, 1)

    #Violations in last 15 minutes (decisions with block/throttle)
    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(
            and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.action.in_(['block', 'throttle'])
            )
        )
    )
    violations = result.scalar() or 0

    #Violations in previous 15 minutes for trend
    prev_15_start = last_60m
    prev_15_end = last_60m + timedelta(minutes=15)
    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(
            and_(
                DecisionLog.created_at >= prev_15_start,
                DecisionLog.created_at < prev_15_end,
                DecisionLog.action.in_(['block', 'throttle'])
            )
        )
    )
    prev_violations = result.scalar() or 0

    #Calculate trend percentage
    if prev_violations > 0:
        violations_trend = int(((violations - prev_violations) / prev_violations) * 100)
    else:
        violations_trend = violations * 100 if violations > 0 else 0
    
    #Suspicious sessions (users with high risk scores in last 15 min)
    result = await db.execute(
        select(DecisionLog.user_id, func.max(DecisionLog.risk_score))
        .where(
            and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score > 0.4  # Lower threshold
            )
        )
        .group_by(DecisionLog.user_id)
    )
    suspicious_sessions = len(result.all())

    #Traffic composition (from last 15 minutes)
    result = await db.execute(
        select(
            func.count(DecisionLog.id),
            DecisionLog.action
        )
        .where(DecisionLog.created_at >= last_15m)
        .group_by(DecisionLog.action)
    )
    action_counts = {row[1]: row[0] for row in result.all()}
    total_actions = sum(action_counts.values())

    traffic_composition = {
        "normal": round((action_counts.get('allow',0) / total_actions) * 100) if total_actions > 0 else 0,
        "bots": round((action_counts.get('throttle', 0) / total_actions) * 100) if total_actions > 0 else 0,
        "suspicious": round((action_counts.get('block', 0) / total_actions) * 100) if total_actions > 0 else 0
    }

    # RPS Trend (compare to previous minute)
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
        sessions_trend=0, #will be calculated if needed later
        traffic_composition=traffic_composition
    )

@router.get("/traffic", response_model=TrafficResponse)
async def get_traffic_data(
    timeframe: str = Query("15m", regex="^(15m|1h|24h)$"),
    db: AsyncSession = Depends(get_db)
):
    # -- Get Traffic data for charts -- #

    now = datetime.utcnow()

    if timeframe == "15m":
        interval = timedelta(minutes=1)
        points = 15
        start_time = now - timedelta(minutes=15)
    elif timeframe == "1h":
        interval = timedelta(minutes=15)
        points = 12
        start_time = now - timedelta(hours=1)
    else: # 24h
        interval = timedelta(hours=1)
        points = 24
        start_time = now - timedelta(hours=24)
    
    data_points = []

    for i in range(points):
        bucket_start = start_time + (interval * i)
        bucket_end = bucket_start + interval

        #Count requests in this bucket
        result = await db.execute(
            select(func.count(RequestLog.id))
            .where(and_(
                RequestLog.created_at >= bucket_start,
                RequestLog.created_at < bucket_end
            ))
        )
        requests = result.scalar() or 0

        # Count anomalies (block/throttle decisions)
        result = await db.execute(
            select(func.count(DecisionLog.id))
            .where(and_(
                DecisionLog.created_at >= bucket_start,
                DecisionLog.created_at < bucket_end,
                DecisionLog.action.in_(['block', 'throttle'])
            ))
        )
        anomalies = result.scalar() or 0

        data_points.append(TrafficDataPoint(
            time=bucket_start,
            requests=requests,
            anomalies=anomalies,
            blocked=0 # if needed, will be tracked separately
        ))
    
    return TrafficResponse(data=data_points, timeframe=timeframe)

@router.get("/suspicious-users", response_model=List[SuspiciousUserResponse])
async def get_suspicious_users(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # -- Get list of suspicious users -- #

    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)

    # Get latest decision per user with high risk score
    subquery = (
        select(
            DecisionLog.user_id,
            func.max(DecisionLog.risk_score).label('max_risk'),
            func.max(DecisionLog.created_at).label('last_seen')
        )
        .where(DecisionLog.created_at >= last_15m)
        .group_by(DecisionLog.user_id)
        .having(func.max(DecisionLog.risk_score) > 0.4)
        .subquery()
    )

    result = await db.execute(
        select(
            subquery.c.user_id,
            subquery.c.max_risk,
            subquery.c.last_seen,
            func.count(DecisionLog.id).label('violations')
        )
        .outerjoin(
            DecisionLog,
            and_(
                DecisionLog.user_id == subquery.c.user_id,
                DecisionLog.created_at >= last_15m,
                DecisionLog.action.in_(['block', 'throttle'])
            )
        )
        .group_by(subquery.c.user_id, subquery.c.max_risk, subquery.c.last_seen)
        .order_by(subquery.c.max_risk.desc())
        .limit(limit)
    )

    suspicious_users = []
    for row in result.all():
        user_id = row[0]
        risk_score = row[1] or 0
        last_seen = row[2]
        violations = row[3] or 0

        # Get user's IP
        ip_result = await db.execute(
            select(RequestLog.ip_address)
            .where(RequestLog.user_id == user_id)
            .order_by(RequestLog.created_at.desc())
            .limit(1)
        )
        ip = ip_result.scalar() or 'unknown'

        # Determine status based on risk score
        if risk_score > 0.85:
            status = 'critical'
        elif risk_score > 0.7:
            status = 'active'
        elif risk_score > 0.6:
            status = 'warning'
        else:
            status = 'monitoring'
    
        suspicious_users.append(SuspiciousUserResponse(
            id=f"user-{user_id}" if user_id else "anonymous",
            violations=violations,
            threat_score=round(risk_score, 2),
            status=status,
            ip=ip,
            last_seen=last_seen
        ))

    return suspicious_users

@router.get("/alerts", response_model=List[AlertResponse])
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # Get recent security alerts

    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)

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
            DecisionLog.action.in_(['block', 'throttle'])
        ))
        .order_by(DecisionLog.risk_score.desc())
        .limit(limit)
    )

    alerts = []
    alert_types = {
        'block': "Blocked Request",
        'throttle': "Rate Limited"
    }

    for idx, row in enumerate(result.all()):
        alerts.append(AlertResponse(
            id=idx + 1,
            ip=row[1] or 'unknown',
            score=round(row[2], 2),
            type=alert_types.get(row[3], row[3]),
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
    # --- Get paginated decision logs --- #

    offset = (page - 1) * limit

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
            DecisionLog.created_at
        )
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .order_by(DecisionLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    logs = []
    for row in result.all():
        logs.append(LogResponse(
            id=row[0],
            request_uuid=row[1],
            user_id=row[2],
            endpoint=row[3],
            ip_address=row[4] or 'unknown',
            action=row[5],
            risk_score=round(row[6], 2) if row[6] else 0,
            explanation=row[7] or "No explanation",
            created_at=row[8]
        ))

    return logs

@router.get("/user/{user_id}", response_model=dict)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # --- Get detailed information about a specific user --- #

    # Get total requests
    result = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.user_id == user_id)
    )

    total_requests = result.scalar() or 0

    # Get violations
    result = await db.execute(
        select(func.count(DecisionLog.id))
        .where(and_(
            DecisionLog.user_id == user_id,
            DecisionLog.action.in_(['block', 'throttle'])
        ))
    )
    violations = result.scalar() or 0

    # Get current risk score (latest)
    result = await db.execute(
        select(DecisionLog.risk_score)
        .where(DecisionLog.user_id == user_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(1)
    )
    current_risk = result.scalar() or 0

    # Get recent actions
    result = await db.execute(
        select(DecisionLog.action, DecisionLog.created_at, DecisionLog.reason)
        .where(DecisionLog.user_id == user_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(10)
    )
    recent_actions = [
        {"action": row[0], "timestamp": row[1], "reason": row[2]}
        for row in result.all()
    ]

    # Get IP history
    result = await db.execute(
        select(RequestLog.ip_address)
        .where(RequestLog.user_id == user_id)
        .distinct()
        .limit(10)
    )
    ip_history = [row[0] for row in result.all() if row[0]]

    # Check if blocked in redis
    is_blocked = await StateManager.is_blocked(user_id)

    return {
        "user_id": user_id,
        "is_anonymous": user_id > 2**60, #Rough heuristic for anonymous fingerprints
        "total_requests": total_requests,
        "violations": violations,
        "current_risk_score": round(current_risk, 2),
        "is_blocked": is_blocked,
        "recent_actions": recent_actions,
        "ip_history": ip_history
    }


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

