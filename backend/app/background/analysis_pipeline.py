"""
app/background/analysis_pipeline.py

Runs AFTER the response has been returned to the client.
Owns ALL heavy work:
  - feature_builder  (5-8 Redis reads)
  - risk_engine      (math + scoring)
  - penalty_manager  (reputation reads/writes)
  - DB logging       (RequestLog, DecisionLog, FeatureLog, MLPrediction)

Writes back to Redis:
  user:{id}:risk_score   → read by fast-path on next request
  user:{id}:blocked      → read by fast-path (hard block)
  user:{id}:throttled    → read by fast-path (soft throttle)
  rep:ip/user/fp         → reputation signals (used in next penalty calc)
"""

import logging
import asyncio

from app.features.feature_builder import FeatureBuilder
from app.risk.risk_engine import compute_risk
from app.policy.penalty_manager import apply_penalty
from app.explainability.explainer import Explainer
from app.state.state_manager import StateManager

from app.db.session import AsyncSessionLocal
from app.db.models.request_log import RequestLog
from app.db.models.decision_log import DecisionLog
from app.db.models.feature_log import FeatureLog
from app.db.models.ml_prediction import MLPrediction

logger = logging.getLogger(__name__)

# Module-level singleton so we don't re-instantiate per request
_feature_builder: FeatureBuilder | None = None


def _get_feature_builder() -> FeatureBuilder:
    global _feature_builder
    if _feature_builder is None:
        _feature_builder = FeatureBuilder(StateManager)
    return _feature_builder


async def run_analysis_pipeline(
    *,
    user_id: int,
    identity,
    signals,
    status_code: int | None,
    request_uuid: str,
    label: str | None,
    fast_risk_score: float,   # the score used for THIS request's decision (for logging)
):
    """
    Full analysis for one request.  Called via asyncio.ensure_future so it
    runs concurrently with (or after) the HTTP response.

    Steps:
        1. Update error counter if status >= 400
        2. Build features  (Redis reads)
        3. Compute risk    (pure math)
        4. Apply penalty   (Redis reads + writes reputation/block flags)
        5. Write risk_score back to Redis   ← feeds next request's fast path
        6. Log to DB
    """
    try:
        # 1. ERROR TRACKING 
        if status_code is not None and status_code >= 400:
            await StateManager.increment_error(user_id)

        #  2. FEATURE BUILDING
        try:
            features = await _get_feature_builder().build(identity, signals)
        except Exception as e:
            logger.error(f"[pipeline] feature_builder failed for user={user_id}: {e}")
            features = _empty_features()

        # 3. RISK SCORING
        try:
            risk_score, label_ml, risk_explanation, contributions = await compute_risk(
                signals, features
            )
            ml_data = {
                "label": label_ml,
                "explanation": risk_explanation,
                "contributions": contributions,
            }
        except Exception as e:
            logger.error(f"[pipeline] risk_engine failed for user={user_id}: {e}")
            risk_score = fast_risk_score  # fall back to whatever fast-path used
            ml_data = {"label": None, "explanation": "fallback", "contributions": {}}

        # 4. PENALTY (writes blocked / throttled / reputation)
        try:
            final_action, penalty_reason, meta = await apply_penalty(
                identity=identity,
                signals=signals,
                risk_score=risk_score,
                base_action=_action_from_score(risk_score),
            )
        except Exception as e:
            logger.error(f"[pipeline] penalty_manager failed for user={user_id}: {e}")
            final_action = "allow"
            penalty_reason = "fallback"
            meta = {}

        # ── 5. WRITE RISK SCORE BACK TO REDIS ────────────────────────────
        #
        # This is the key step.  The fast-path on the NEXT request from this
        # user will read this value and make its decision in <5ms.
        #
        # TTL = 5 minutes.  If a user goes quiet, the score naturally expires
        # and they start fresh.
        #
        '''await StateManager.set(f"user:{user_id}:risk_score", round(risk_score, 4), ttl=300)

        # Write soft throttle flag if needed (separate from block flag which
        # penalty_manager writes directly via block_user / block_ip)
        if final_action == "throttle":
            await StateManager.set(f"user:{user_id}:throttled", "1", ttl=60)
        else:
            # Clear throttle flag on clean requests so it doesn't stick forever
            await StateManager.delete(f"user:{user_id}:throttled")'''

        # 6. DB LOGGING
        explanation = Explainer.generate(
            action=final_action,
            reason=penalty_reason,
            risk_score=risk_score,
            features=features,
            ml_data=ml_data,
        )

        await _log_to_db(
            user_id=user_id,
            identity=identity,
            signals=signals,
            features=features,
            action=final_action,
            reason=penalty_reason,
            risk_score=risk_score,
            ml_data=ml_data,
            explanation=explanation,
            request_uuid=request_uuid,
            status_code=status_code or 200,
            label=label,
        )

        logger.debug(
            f"[pipeline] done user={user_id} | risk={risk_score:.3f} | "
            f"action={final_action} | req_uuid={request_uuid}"
        )

    except Exception as e:
        logger.exception(f"[pipeline] unhandled error for user={user_id}: {e}")


#  DB LOGGING 

async def _log_to_db(
    *,
    user_id,
    identity,
    signals,
    features,
    action,
    reason,
    risk_score,
    ml_data,
    explanation,
    request_uuid,
    status_code,
    label,
):

    try:
        async with AsyncSessionLocal() as db:
            # Update API key last_used_at timestamp if request used one
            if identity.api_key:
                from sqlalchemy import update
                from app.db.models.api_key import APIKey
                from datetime import datetime
                await db.execute(
                    update(APIKey)
                    .where(APIKey.key == identity.api_key)
                    .values(last_used_at=datetime.utcnow())
                )

            request_log = RequestLog(
                user_id=user_id,
                endpoint=signals.endpoint,
                ip_address=signals.ip_address,
                user_agent=signals.user_agent,
                status_code=status_code,
                request_uuid=request_uuid,
            )
            db.add(request_log)
            await db.flush()
            request_id = request_log.id

            db.add(DecisionLog(
                user_id=user_id,
                request_id=request_id,
                action=action,
                reason=reason,
                risk_score=risk_score,
                explanation=explanation.get("summary"),
                explanation_json=explanation,
                ground_truth_label=label,
                request_uuid=request_uuid,
            ))

            db.add(FeatureLog(
                user_id=user_id,
                request_id=request_id,
                request_uuid=request_uuid,
                features=features,
                behavioral_features={
                    "req_per_min": features.get("req_per_min"),
                    "req_per_sec": features.get("req_per_sec"),
                    "burst_score": features.get("burst_score"),
                },
                pattern_features={
                    "endpoint_entropy": features.get("endpoint_entropy"),
                },
                identity_features={
                    "ip_changes": features.get("ip_changes"),
                    "is_bot": features.get("is_bot"),
                },
            ))

            if ml_data and ml_data.get("label"):
                db.add(MLPrediction(
                    user_id=user_id,
                    request_id=request_id,
                    risk_score=risk_score,
                    risk_label=ml_data.get("label"),
                    explanation=explanation.get("summary"),
                    feature_contributions=explanation.get("feature_contributions"),
                    request_uuid=request_uuid,
                ))

            await db.commit()

    except Exception as e:
        logger.error(f"[pipeline] DB logging failed for user={user_id}: {e}")


# HELPERS

def _action_from_score(risk_score: float) -> str:
    """Derive a base action from risk score for penalty_manager input."""
    if risk_score > 0.85:
        return "block"
    if risk_score > 0.5:
        return "throttle"
    return "allow"


def _empty_features() -> dict:
    """Safe default when feature_builder fails."""
    return {
        "req_per_sec": 0,
        "req_per_min": 0,
        "unique_endpoints": None,
        "endpoint_entropy": 0.0,
        "error_rate": 0.0,
        "burst_score": 0.0,
        "is_rate_limited": 0,
        "is_burst": 0,
        "is_suspicious_ua": 0,
        "ip_changes": 0,
        "request_regularity": 0.0,
        "is_bot": 0,
        "is_browser": 0,
        "time_variance": 0.0,
        "time_mean": 0.0,
        "ip_address": "unknown",
    }