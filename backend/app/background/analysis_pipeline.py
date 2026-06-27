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

_feature_builder: FeatureBuilder | None = None


def _get_feature_builder() -> FeatureBuilder:
    global _feature_builder
    if _feature_builder is None:
        _feature_builder = FeatureBuilder(StateManager)
    return _feature_builder


async def run_analysis_pipeline(
    *,
    identity,
    signals,
    status_code: int | None,
    request_uuid: str,
    label: str | None,
    fast_risk_score: float,
):
    try:
        # ── 1. ERROR TRACKING ─────────────────────────────────────────────
        if status_code is not None and status_code >= 400:
            await StateManager.increment_error(identity)

        # ── 2. FEATURE BUILDING ───────────────────────────────────────────
        try:
            features = await _get_feature_builder().build(identity, signals)
        except Exception as e:
            logger.error(
                f"[pipeline] feature_builder failed for identity={identity.identity_id}: {e}"
            )
            features = _empty_features()

        # ── 3. RISK SCORING ───────────────────────────────────────────────
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
            logger.error(
                f"[pipeline] risk_engine failed for identity={identity.identity_id}: {e}"
            )
            risk_score = fast_risk_score
            ml_data = {"label": None, "explanation": "fallback", "contributions": {}}

        # ── 4. PENALTY ────────────────────────────────────────────────────
        try:
            final_action, penalty_reason, meta = await apply_penalty(
                identity=identity,
                signals=signals,
                risk_score=risk_score,
                base_action=_action_from_score(risk_score),
            )
        except Exception as e:
            logger.error(
                f"[pipeline] penalty_manager failed for identity={identity.identity_id}: {e}"
            )
            final_action = "allow"
            penalty_reason = "fallback"
            meta = {}

        # ── 5. REDIS WRITE (kept commented, but FIXED) ────────────────────
        '''
        base = f"client:{identity.client_id}:identity:{identity.identity_id}"

        await StateManager.set(f"{base}:risk_score", round(risk_score, 4), ttl=300)

        if final_action == "throttle":
            await StateManager.set(f"{base}:throttled", "1", ttl=60)
        else:
            await StateManager.delete(f"{base}:throttled")
        '''

        # ── 6. DB LOGGING ─────────────────────────────────────────────────
        explanation = Explainer.generate(
            action=final_action,
            reason=penalty_reason,
            risk_score=risk_score,
            features=features,
            ml_data=ml_data,
        )

        await _log_to_db(
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
            f"[pipeline] done identity={identity.identity_id} | "
            f"risk={risk_score:.3f} | action={final_action} | req_uuid={request_uuid}"
        )

    except Exception as e:
        logger.exception(
            f"[pipeline] unhandled error for identity={identity.identity_id}: {e}"
        )


# ── DB LOGGING ──────────────────────────────────────────────────────────────

async def _log_to_db(
    *,
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
            api_key_id = getattr(identity, "api_key_id", None)
            request_log = RequestLog(
                identity_id=identity.identity_id,
                client_id=identity.client_id,
                api_key_id=api_key_id,
                endpoint=signals.endpoint,
                method=getattr(signals, "method", None),
                ip_address=signals.ip_address,
                user_agent=signals.user_agent,
                status_code=status_code,
                action=action,
                request_uuid=request_uuid,
            )
            db.add(request_log)
            await db.flush()
            request_id = request_log.id

            db.add(DecisionLog(
                identity_id=identity.identity_id,
                client_id=identity.client_id,
                api_key_id=api_key_id,
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
                identity_id=identity.identity_id,
                client_id=identity.client_id,
                api_key_id=api_key_id,
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
                    identity_id=identity.identity_id,
                    client_id=identity.client_id,
                    api_key_id=api_key_id,
                    request_id=request_id,
                    risk_score=risk_score,
                    risk_label=ml_data.get("label"),
                    explanation=explanation.get("summary"),
                    feature_contributions=explanation.get("feature_contributions"),
                    request_uuid=request_uuid,
                ))

            await db.commit()

    except Exception as e:
        logger.error(
            f"[pipeline] DB logging failed for identity={identity.identity_id}: {e}"
        )


# ── HELPERS ─────────────────────────────────────────────────────────────────

def _action_from_score(risk_score: float) -> str:
    if risk_score > 0.85:
        return "block"
    if risk_score > 0.5:
        return "throttle"
    return "allow"


def _empty_features() -> dict:
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