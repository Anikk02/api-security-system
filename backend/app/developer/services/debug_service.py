"""
Business logic for Debug Tools.
Joins RequestLog with DecisionLog and FeatureLog by request_id — 
surfacing the exact same explainability data the Security Engine 
already writes (see app/explainability/explainer.py), without
duplicating any of that logic here.
"""
import logging
from datetime import datetime

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog
from app.db.models.feature_log import FeatureLog
from app.state.state_manager import StateManager
from app.websocket.developer_manager import developer_websocket_manager

logger = logging.getLogger(__name__)


class _IdentityRef:
    """Minimal stand-in for app.identity.resolver.Identity (same pattern as dashboard.py)."""
    __slots__ = ("client_id", "identity_id")

    def __init__(self, client_id: int | None, identity_id: str):
        self.client_id = client_id
        self.identity_id = identity_id


async def get_request_debug(
    db: AsyncSession, 
    request_log_id: int,
    broadcast: bool = False
) -> dict | None:
    """Full lifecycle for one request: RequestLog + DecisionLog + FeatureLog."""
    log_result = await db.execute(select(RequestLog).where(RequestLog.id == request_log_id))
    request_log = log_result.scalar_one_or_none()
    if not request_log:
        return None

    decision_result = await db.execute(
        select(DecisionLog).where(DecisionLog.request_id == request_log_id)
    )
    decision = decision_result.scalar_one_or_none()

    feature_result = await db.execute(
        select(FeatureLog).where(FeatureLog.request_id == request_log_id)
    )
    feature_log = feature_result.scalar_one_or_none()

    decision_dict = None
    if decision:
        decision_dict = {
            "id": decision.id,
            "request_uuid": decision.request_uuid,
            "identity_id": decision.identity_id,
            "client_id": decision.client_id,
            "api_key_id": decision.api_key_id,
            "action": decision.action,
            "reason": decision.reason,
            "risk_score": decision.risk_score,
            "ground_truth_label": decision.ground_truth_label,
            "explanation": decision.explanation,
            "explanation_json": decision.explanation_json,
            "created_at": decision.created_at,
        }

    features_dict = None
    if feature_log:
        features_dict = {
            "features": feature_log.features,
            "behavioral_features": feature_log.behavioral_features,
            "pattern_features": feature_log.pattern_features,
            "identity_features": feature_log.identity_features,
        }

    result = {
        "request_log": request_log,
        "decision": decision_dict,
        "features": features_dict,
    }

    # Broadcast debug info if a suspicious pattern is detected
    if broadcast and decision_dict and decision_dict.get("action") == "block":
        await developer_websocket_manager.broadcast_abuse_alert({
            "type": "debug_insight",
            "request_id": request_log_id,
            "identity_id": request_log.identity_id,
            "client_id": request_log.client_id,
            "action": decision_dict.get("action"),
            "risk_score": decision_dict.get("risk_score"),
            "reason": decision_dict.get("reason"),
            "explanation": decision_dict.get("explanation"),
            "timestamp": datetime.utcnow().isoformat()
        })

    return result


async def get_identity_debug_summary(
    db: AsyncSession, 
    identity_id: str,
    broadcast: bool = False
) -> dict | None:
    """Counts, recent decisions, and live Redis block state for one identity_id."""
    total_result = await db.execute(
        select(func.count(RequestLog.id)).where(RequestLog.identity_id == identity_id)
    )
    total = total_result.scalar() or 0
    if total == 0:
        return None

    client_result = await db.execute(
        select(RequestLog.client_id)
        .where(RequestLog.identity_id == identity_id)
        .order_by(RequestLog.created_at.desc())
        .limit(1)
    )
    client_id = client_result.scalar()

    counts_result = await db.execute(
        select(
            func.sum(case((RequestLog.action == "block", 1), else_=0)).label("blocked"),
            func.sum(case((RequestLog.action == "throttle", 1), else_=0)).label("throttled"),
            func.sum(case((RequestLog.action == "allow", 1), else_=0)).label("allowed"),
        ).where(RequestLog.identity_id == identity_id)
    )
    counts_row = counts_result.one()

    recent_result = await db.execute(
        select(DecisionLog)
        .where(DecisionLog.identity_id == identity_id)
        .order_by(DecisionLog.created_at.desc())
        .limit(20)
    )
    recent_decisions = [
        {
            "id": d.id,
            "action": d.action,
            "risk_score": d.risk_score,
            "reason": d.reason,
            "explanation": d.explanation,
            "created_at": d.created_at,
        }
        for d in recent_result.scalars().all()
    ]

    # Reuses the exact same StateManager.is_blocked() the client dashboard
    # already calls in app/api/routes/dashboard.py:get_user_details().
    is_blocked = await StateManager.is_blocked(_IdentityRef(client_id, identity_id))

    result = {
        "identity_id": identity_id,
        "client_id": client_id,
        "total_requests": total,
        "blocked_count": counts_row.blocked or 0,
        "throttled_count": counts_row.throttled or 0,
        "allowed_count": counts_row.allowed or 0,
        "is_blocked": is_blocked,
        "recent_decisions": recent_decisions,
    }

    # Broadcast identity debug info if identity is blocked or has high block rate
    if broadcast:
        block_rate = (counts_row.blocked or 0) / total if total > 0 else 0
        if is_blocked or block_rate > 0.5:  # More than 50% blocked requests
            await developer_websocket_manager.broadcast_abuse_alert({
                "type": "identity_flagged",
                "identity_id": identity_id,
                "client_id": client_id,
                "is_blocked": is_blocked,
                "block_rate": round(block_rate * 100, 2),
                "total_requests": total,
                "blocked_count": counts_row.blocked or 0,
                "throttled_count": counts_row.throttled or 0,
                "allowed_count": counts_row.allowed or 0,
                "timestamp": datetime.utcnow().isoformat()
            })

    return result