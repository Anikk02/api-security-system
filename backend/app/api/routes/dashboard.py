import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
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
from app.db.models.client import Client
from app.risk.risk_engine import get_adaptive_thresholds
from app.state.state_manager import StateManager
from app.authentication.dependencies import require_active_client

from app.authentication.dependencies import require_active_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_active_client)]
)


class _IdentityRef:
    """Minimal stand-in for app.identity.resolver.Identity."""
    __slots__ = ("client_id", "identity_id")

    def __init__(self, client_id: int | None, identity_id: str):
        self.client_id = client_id
        self.identity_id = identity_id


async def _resolve_client_id(db: AsyncSession, identity_id: str, client_id: int | None) -> int | None:
    """Resolve client_id from identity_id if not provided."""
    if client_id is not None:
        return client_id

    result = await db.execute(
        select(RequestLog.client_id)
        .where(RequestLog.identity_id == identity_id)
        .order_by(RequestLog.created_at.desc())
        .limit(1)
    )
    return result.scalar()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard stats for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
    now = datetime.utcnow()
    last_minute = now - timedelta(minutes=1)
    prev_minute_start = last_minute - timedelta(minutes=1)
    last_15m = now - timedelta(minutes=15)
    last_60m = now - timedelta(minutes=60)
    prev_15_start = last_60m
    prev_15_end = last_60m + timedelta(minutes=15)

    high_th, med_th = get_adaptive_thresholds()

    # ── 1 query: RPS (current) + RPS (previous minute) ──────────
    rps_result = await db.execute(
        select(
            func.sum(case((and_(
                RequestLog.created_at >= last_minute,
                RequestLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("current"),
            func.sum(case((and_(
                RequestLog.created_at >= prev_minute_start,
                RequestLog.created_at < last_minute,
                RequestLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("previous"),
        )
        .where(RequestLog.created_at >= prev_minute_start)
    )
    rps_row = rps_result.one()
    requests_last_minute = rps_row.current or 0
    prev_requests = rps_row.previous or 0

    requests_per_second = round(requests_last_minute / 60, 1)
    prev_rps = prev_requests / 60
    rps_trend = round(((requests_per_second - prev_rps) / (prev_rps + 0.01)) * 100, 1)

    # ── 2 query: violations + risk composition ───────────
    dec_result = await db.execute(
        select(
            # Current violations (last 15m, medium + high risk)
            func.sum(case((and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score > med_th,
                DecisionLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("violations"),
            # Previous violations
            func.sum(case((and_(
                DecisionLog.created_at >= prev_15_start,
                DecisionLog.created_at < prev_15_end,
                DecisionLog.risk_score > med_th,
                DecisionLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("prev_violations"),
            # Risk composition buckets
            func.sum(case((and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score > high_th,
                DecisionLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("high_count"),
            func.sum(case((and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score > med_th,
                DecisionLog.risk_score <= high_th,
                DecisionLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("medium_count"),
            func.sum(case((and_(
                DecisionLog.created_at >= last_15m,
                DecisionLog.risk_score <= med_th,
                DecisionLog.client_id == client_id  # ✅ Filter
            ), 1), else_=0)).label("low_count"),
        )
        .where(DecisionLog.created_at >= prev_15_start)
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
        "normal": round((low_count / total) * 100) if total else 0,
        "suspicious": round((medium_count / total) * 100) if total else 0,
        "high_risk": round((high_count / total) * 100) if total else 0,
    }

    # ── 3 query: suspicious sessions ───────────
    sess_result = await db.execute(
        select(func.count(func.distinct(RequestLog.identity_id)))
        .select_from(DecisionLog)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > med_th,
            RequestLog.identity_id.isnot(None),
            RequestLog.client_id == client_id  # ✅ Filter
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
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    timeframe: str = Query("15m", regex="^(15m|1h|24h)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get traffic data for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
    now = datetime.utcnow()
    high_th, _ = get_adaptive_thresholds()

    if timeframe == "15m":
        trunc_unit = "minute"
        points = 15
        start_time = now - timedelta(minutes=15)
        interval_minutes = 1
    elif timeframe == "1h":
        trunc_unit = "minute"
        points = 12
        start_time = now - timedelta(hours=1)
        interval_minutes = 5
    else:  # 24h
        trunc_unit = "hour"
        points = 24
        start_time = now - timedelta(hours=24)
        interval_minutes = 60

    # ── Single query per table: DB aggregates ───────────────────
    request_rows = (await db.execute(
        select(
            func.date_trunc(trunc_unit, RequestLog.created_at).label("bucket"),
            func.count().label("cnt")
        )
        .where(and_(
            RequestLog.created_at >= start_time,
            RequestLog.client_id == client_id  # ✅ Filter
        ))
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
            DecisionLog.risk_score > high_th,
            DecisionLog.client_id == client_id  # ✅ Filter
        ))
        .group_by("bucket")
        .order_by("bucket")
    )).all()

    req_by_bucket = {row.bucket: row.cnt for row in request_rows}
    anom_by_bucket = {row.bucket: row.cnt for row in decision_rows}

    data_points = []
    for i in range(points):
        bucket_start = start_time + timedelta(minutes=interval_minutes * i)
        bucket_end = bucket_start + timedelta(minutes=interval_minutes)

        if timeframe == "1h":
            requests = sum(
                v for k, v in req_by_bucket.items()
                if bucket_start <= k < bucket_end
            )
            anomalies = sum(
                v for k, v in anom_by_bucket.items()
                if bucket_start <= k < bucket_end
            )
        else:
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
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get suspicious users for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    high_th, med_th = get_adaptive_thresholds()

    result = await db.execute(
        select(
            RequestLog.identity_id.label("identity_id"),
            func.min(RequestLog.ip_address).label("ip"),
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
            RequestLog.identity_id.isnot(None),
            RequestLog.client_id == client_id  # ✅ Filter
        ))
        .group_by(RequestLog.identity_id)
        .having(func.max(DecisionLog.risk_score) > med_th)
        .order_by(func.max(DecisionLog.risk_score).desc())
        .limit(limit)
    )

    suspicious_users = []
    for row in result.all():
        identity_id = row.identity_id
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
            id=identity_id,
            identity_id=identity_id,
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
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
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
            DecisionLog.identity_id
        )
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            DecisionLog.created_at >= last_15m,
            DecisionLog.risk_score > high_th,
            RequestLog.client_id == client_id  # ✅ Filter
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
            identity_id=row[6],
        ))

    return alerts


@router.get("/logs", response_model=List[LogResponse])
async def get_decision_logs(
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get logs for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
    offset = (page - 1) * limit
    high_th, med_th = get_adaptive_thresholds()

    result = await db.execute(
        select(
            DecisionLog.id,
            DecisionLog.request_uuid,
            DecisionLog.identity_id,
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
        .where(RequestLog.client_id == client_id)  # ✅ Filter
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
            identity_id=row[2],
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
    user_id: str,
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    client_id: int | None = Query(None, description="Client/tenant ID that owns this identity, if known"),
    db: AsyncSession = Depends(get_db)
):
    """Get user details for the authenticated client only."""
    auth_client_id = current_client.id  # ✅ The authenticated client
    
    identity_id = user_id
    
    # ✅ Ensure the user belongs to the authenticated client
    if client_id is not None and client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Access denied to this client's data")
    
    now = datetime.utcnow()
    last_15m = now - timedelta(minutes=15)
    high_th, med_th = get_adaptive_thresholds()

    # ── Verify user belongs to this client ──
    if client_id is None:
        result = await db.execute(
            select(RequestLog.client_id)
            .where(RequestLog.identity_id == identity_id)
            .order_by(RequestLog.created_at.desc())
            .limit(1)
        )
        resolved_client_id = result.scalar()
        if resolved_client_id is not None and resolved_client_id != auth_client_id:
            raise HTTPException(status_code=403, detail="Access denied to this user's data")
        client_id = resolved_client_id

    # ── 1 query: total requests ──
    total_result = await db.execute(
        select(func.count(RequestLog.id))
        .where(and_(
            RequestLog.identity_id == identity_id,
            RequestLog.client_id == auth_client_id  # ✅ Filter
        ))
    )
    total_requests = total_result.scalar() or 0

    # ── 2 query: violations and risk ──
    risk_result = await db.execute(
        select(
            func.sum(case((DecisionLog.risk_score > med_th, 1), else_=0)).label("violations"),
            func.max(DecisionLog.risk_score).label("max_risk"),
            func.avg(DecisionLog.risk_score).label("avg_risk"),
        )
        .where(and_(
            DecisionLog.identity_id == identity_id,
            DecisionLog.created_at >= last_15m,
            DecisionLog.client_id == auth_client_id  # ✅ Filter
        ))
    )
    risk_row = risk_result.one()
    
    violations = risk_row.violations or 0
    current_risk = risk_row.max_risk or 0
    avg_risk = risk_row.avg_risk or 0

    # ── 3 query: recent actions ──
    actions_result = await db.execute(
        select(DecisionLog.action, DecisionLog.created_at,
               DecisionLog.reason, DecisionLog.risk_score)
        .where(and_(
            DecisionLog.identity_id == identity_id,
            DecisionLog.client_id == auth_client_id  # ✅ Filter
        ))
        .order_by(DecisionLog.created_at.desc())
        .limit(10)
    )
    recent_actions = [
        {"action": row[0], "timestamp": row[1], "reason": row[2], "risk_score": row[3]}
        for row in actions_result.all()
    ]

    # ── 4 query: IP history ──
    ip_result = await db.execute(
        select(RequestLog.ip_address)
        .where(and_(
            RequestLog.identity_id == identity_id,
            RequestLog.client_id == auth_client_id  # ✅ Filter
        ))
        .distinct()
        .limit(10)
    )
    ip_history = [row[0] for row in ip_result.all() if row[0]]

    # ── Redis: block state ──
    is_blocked = await StateManager.is_blocked(_IdentityRef(client_id, identity_id))

    return {
        "identity_id": identity_id,
        "client_id": client_id,
        "is_anonymous": client_id is None,
        "total_requests": total_requests,
        "violations": violations,
        "current_risk_score": round(current_risk, 2),
        "avg_risk_score": round(avg_risk, 2),
        "is_blocked": is_blocked,
        "recent_actions": recent_actions,
        "ip_history": ip_history,
    }


@router.get("/ip/{ip}/trend")
async def get_ip_trend(
    ip: str,
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    db: AsyncSession = Depends(get_db)
):
    """Get IP trend data for the authenticated client only."""
    client_id = current_client.id  # ✅ Filter by this client
    
    last_1h = datetime.utcnow() - timedelta(hours=1)

    result = await db.execute(
        select(DecisionLog.created_at, DecisionLog.risk_score)
        .join(RequestLog, DecisionLog.request_id == RequestLog.id)
        .where(and_(
            RequestLog.ip_address == ip,
            DecisionLog.created_at >= last_1h,
            RequestLog.client_id == client_id  # ✅ Filter
        ))
        .order_by(DecisionLog.created_at)
    )

    return [{"time": row[0], "risk": row[1]} for row in result.all()]


@router.post("/user/{user_id}/block")
async def block_user(
    user_id: str,
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    duration: int = Query(3600, description="Block duration in seconds"),
    client_id: int | None = Query(None, description="Client/tenant ID that owns this identity, if known"),
    db: AsyncSession = Depends(get_db)
):
    """Block an identity for the specified duration."""
    auth_client_id = current_client.id
    identity_id = user_id
    
    # ✅ Verify user belongs to this client
    resolved_client_id = await _resolve_client_id(db, identity_id, client_id)
    if resolved_client_id is not None and resolved_client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Access denied to this user")
    
    try:
        await StateManager.block_identity(_IdentityRef(resolved_client_id, identity_id), duration)
        logger.info(f"Identity {identity_id} blocked for {duration} seconds by client {auth_client_id}")
        return {
            "success": True,
            "message": f"Identity {identity_id} blocked for {duration} seconds",
            "identity_id": identity_id,
            "duration": duration,
        }
    except Exception as e:
        logger.error(f"Failed to block identity {identity_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/user/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    client_id: int | None = Query(None, description="Client/tenant ID that owns this identity, if known"),
    db: AsyncSession = Depends(get_db)
):
    """Unblock an identity."""
    auth_client_id = current_client.id
    identity_id = user_id
    
    # ✅ Verify user belongs to this client
    resolved_client_id = await _resolve_client_id(db, identity_id, client_id)
    if resolved_client_id is not None and resolved_client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Access denied to this user")
    
    try:
        base = StateManager._base(resolved_client_id, identity_id)
        await StateManager.delete(f"{base}:blocked")
        logger.info(f"Identity {identity_id} unblocked by client {auth_client_id}")
        return {
            "success": True,
            "message": f"Identity {identity_id} unblocked",
            "identity_id": identity_id,
        }
    except Exception as e:
        logger.error(f"Failed to unblock identity {identity_id}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/user/{user_id}/warning")
async def send_warning(
    user_id: str,
    current_client: Client = Depends(require_active_client),  # ✅ Authentication
    message: str = Query(
        "Suspicious activity detected on your account",
        description="Warning message"
    ),
    client_id: int | None = Query(None, description="Client/tenant ID that owns this identity, if known"),
    db: AsyncSession = Depends(get_db)
):
    """Send a warning to an identity (logs the warning)."""
    auth_client_id = current_client.id
    identity_id = user_id
    
    # ✅ Verify user belongs to this client
    resolved_client_id = await _resolve_client_id(db, identity_id, client_id)
    if resolved_client_id is not None and resolved_client_id != auth_client_id:
        raise HTTPException(status_code=403, detail="Access denied to this user")
    
    try:
        warning_log = WarningLog(
            identity_id=identity_id,
            client_id=resolved_client_id,
            message=message,
            created_at=datetime.utcnow(),
        )
        db.add(warning_log)
        await db.commit()
        logger.info(f"Warning sent to identity {identity_id} by client {auth_client_id}")
        return {
            "success": True,
            "message": f"Warning sent to identity {identity_id}",
            "identity_id": identity_id,
            "warning_message": message,
        }
    except Exception as e:
        logger.error(f"Failed to send warning to identity {identity_id}: {e}")
        return {"success": False, "error": str(e)}