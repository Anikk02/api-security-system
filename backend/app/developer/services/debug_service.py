"""
Business logic for Debug Tools.
Joins RequestLog with DecisionLog, FeatureLog, and MLPrediction by
request_id — surfacing the exact same explainability data the Security
Engine already writes (see app/explainability/explainer.py), without
duplicating any of that logic here.
"""
import logging

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog
from app.db.models.feature_log import FeatureLog
from app.db.models.ml_prediction import MLPrediction
from app.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class _IdentityRef:
    """Minimal stand-in for app.identity.resolver.Identity (same pattern as dashboard.py)."""
    __slots__ = ("client_id", "identity_id")

    def __init__(self, client_id: int | None, identity_id: str):
        self.client_id = client_id
        self.identity_id = identity_id


async def get_request_debug(db: AsyncSession, request_log_id: int) -> dict | None:
    """Full lifecycle for one request: RequestLog + DecisionLog + FeatureLog + MLPrediction."""
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

    ml_result = await db.execute(
        select(MLPrediction).where(MLPrediction.request_id == request_log_id)
    )
    ml_prediction = ml_result.scalar_one_or_none()

    decision_dict = None
    if decision:
        decision_dict = {
            "id": decision.id,
            "action": decision.action,
            "reason": decision.reason,
            "risk_score": decision.risk_score,
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

    ml_dict = None
    if ml_prediction:
        ml_dict = {
            "risk_score": ml_prediction.risk_score,
            "risk_label": ml_prediction.risk_label,
            "feature_contributions": ml_prediction.feature_contributions,
            "explanation": ml_prediction.explanation,
            "model_version": ml_prediction.model_version,
        }

    return {
        "request_log": request_log,
        "decision": decision_dict,
        "features": features_dict,
        "ml_prediction": ml_dict,
    }


async def get_identity_debug_summary(db: AsyncSession, identity_id: str) -> dict | None:
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
            "created_at": d.created_at,
        }
        for d in recent_result.scalars().all()
    ]

    # Reuses the exact same StateManager.is_blocked() the client dashboard
    # already calls in app/api/routes/dashboard.py:get_user_details().
    is_blocked = await StateManager.is_blocked(_IdentityRef(client_id, identity_id))

    return {
        "identity_id": identity_id,
        "client_id": client_id,
        "total_requests": total,
        "blocked_count": counts_row.blocked or 0,
        "throttled_count": counts_row.throttled or 0,
        "allowed_count": counts_row.allowed or 0,
        "is_blocked": is_blocked,
        "recent_decisions": recent_decisions,
    }
