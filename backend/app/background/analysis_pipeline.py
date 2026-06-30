import logging

from app.features.feature_builder import FeatureBuilder
from app.risk.risk_engine import compute_risk
from app.policy.penalty_manager import apply_penalty
from app.policy.decision import PenaltyDecision
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
    fast_action: str | None = None,  # Action from fast path (what actually happened)
):
    try:
        logger.info(
            f"[pipeline] CALLED: identity={identity.identity_id}, "
            f"status_code={status_code}, "
            f"fast_risk_score={fast_risk_score}, "
            f"fast_action={fast_action}, "
            f"request_uuid={request_uuid}"
        )
        
        # -------------------------------------------------------
        # Track Errors
        # -------------------------------------------------------
        if status_code is not None and status_code >= 400:
            await StateManager.increment_error(identity)

        # -------------------------------------------------------
        # Build Features
        # -------------------------------------------------------
        try:
            features = await _get_feature_builder().build(
                identity,
                signals,
            )
        except Exception as e:
            logger.exception(f"[pipeline] FeatureBuilder failed: {e}")
            features = _empty_features()

        # -------------------------------------------------------
        # Compute Risk (for current request)
        # -------------------------------------------------------
        try:
            (
                risk_score,
                risk_label,
                explanation,
                contributions,
            ) = await compute_risk(signals, features)

            risk_data = {
                "label": risk_label,
                "explanation": explanation,
                "contributions": contributions,
            }
        except Exception as e:
            logger.exception(f"[pipeline] RiskEngine failed: {e}")
            risk_score = fast_risk_score
            risk_data = {
                "label": "low",
                "explanation": "fallback",
                "contributions": {},
            }

        # -------------------------------------------------------
        # 🔥 ALWAYS run penalty manager with CURRENT risk score
        # This updates Redis for future requests
        # -------------------------------------------------------
        try:
            penalty_decision: PenaltyDecision = await apply_penalty(
                identity=identity,
                signals=signals,
                risk_score=risk_score,  # CURRENT computed risk
            )
            logger.debug(
                f"[pipeline] PenaltyManager: action={penalty_decision.action}, "
                f"risk={penalty_decision.risk_score:.3f}"
            )
        except Exception as e:
            logger.exception(f"[pipeline] PenaltyManager failed: {e}")
            penalty_decision = PenaltyDecision(
                action="allow",
                reason="Penalty fallback",
                risk_score=risk_score,
                trust_score=1.0,
                reputation=0.0,
            )

        # -------------------------------------------------------
        # 🔥 LOG what actually happened (fast path decision)
        # -------------------------------------------------------
        # The fast path decision is what happened to THIS request
        # Use it for logging, separate from penalty_decision
        log_action = fast_action if fast_action in ["block", "throttle"] else penalty_decision.action
        log_reason = f"Fast path: {fast_action}" if fast_action in ["block", "throttle"] else penalty_decision.reason
        log_risk_score = fast_risk_score if fast_action in ["block", "throttle"] else penalty_decision.risk_score

        logger.info(
            f"[pipeline] Logging: action={log_action}, "
            f"(penalty_manager said: {penalty_decision.action})"
        )

        # -------------------------------------------------------
        # Explainability - Use log data for explanation
        # -------------------------------------------------------
        explanation_json = Explainer.generate(
            action=log_action,
            reason=log_reason,
            risk_score=log_risk_score,
            features=features,
            risk_data=risk_data,
        )

        # -------------------------------------------------------
        # DB Logging - Log what actually happened (fast path decision)
        # -------------------------------------------------------
        await _log_to_db(
            identity=identity,
            signals=signals,
            features=features,
            action=log_action,           # Fast path decision
            reason=log_reason,
            risk_score=log_risk_score,
            risk_data=risk_data,
            explanation=explanation_json,
            request_uuid=request_uuid,
            status_code=status_code or 200,
            label=label,
            penalty_action=penalty_decision.action,  # For debugging
            penalty_risk=penalty_decision.risk_score,
        )

        logger.debug(
            f"[pipeline] COMPLETED: identity={identity.identity_id} | "
            f"LOG_ACTION={log_action} | "
            f"PENALTY_ACTION={penalty_decision.action} | "
            f"computed_risk={risk_score:.3f}"
        )

    except Exception as e:
        logger.exception(
            f"[pipeline] Unhandled exception "
            f"identity={identity.identity_id}, "
            f"error={e}"
        )


async def _log_to_db(
    *,
    identity,
    signals,
    features,
    action: str,           # Fast path decision (what actually happened)
    reason: str,
    risk_score: float,
    risk_data,
    explanation,
    request_uuid,
    status_code,
    label,
    penalty_action: str = None,  # For debugging
    penalty_risk: float = None,
):
    try:
        async with AsyncSessionLocal() as db:
            api_key_id = getattr(identity, "api_key_id", None)

            # Create RequestLog with fast path decision
            request_log = RequestLog(
                identity_id=identity.identity_id,
                client_id=identity.client_id,
                api_key_id=api_key_id,
                endpoint=signals.endpoint,
                method=getattr(signals, "method", None),
                ip_address=signals.ip_address,
                user_agent=signals.user_agent,
                status_code=status_code,
                action=action,  # Fast path decision
                request_uuid=request_uuid,
            )
            db.add(request_log)
            await db.flush()

            request_id = request_log.id

            # Create DecisionLog with fast path decision
            db.add(
                DecisionLog(
                    identity_id=identity.identity_id,
                    client_id=identity.client_id,
                    api_key_id=api_key_id,
                    request_id=request_id,
                    action=action,  # Fast path decision
                    reason=reason,
                    risk_score=risk_score,
                    explanation=explanation.get("summary"),
                    explanation_json=explanation,
                    ground_truth_label=label,
                    request_uuid=request_uuid,
                )
            )

            # Create FeatureLog
            db.add(
                FeatureLog(
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
                )
            )

            # Create MLPrediction if available
            if risk_data.get("label"):
                db.add(
                    MLPrediction(
                        identity_id=identity.identity_id,
                        client_id=identity.client_id,
                        api_key_id=api_key_id,
                        request_id=request_id,
                        risk_score=risk_score,
                        risk_label=risk_data.get("label"),
                        explanation=explanation.get("summary"),
                        feature_contributions=explanation.get("feature_contributions"),
                        request_uuid=request_uuid,
                    )
                )

            await db.commit()
            logger.debug(f"[_log_to_db] Success for request_uuid={request_uuid}")

    except Exception as e:
        logger.exception(f"[_log_to_db] DB logging failed: {e}")
        raise


def _empty_features() -> dict:
    return {
        "req_per_sec": 0.0,
        "req_per_min": 0.0,
        "burst_score": 0.0,
        "unique_endpoints": 0,
        "endpoint_entropy": 0.0,
        "top_endpoint_ratio": 0.0,
        "error_rate": 0.0,
        "is_rate_limited": False,
        "ip_changes": 0,
        "is_bot": False,
        "is_browser": False,
        "is_suspicious_ua": False,
        "request_regularity": 0.0,
        "time_variance": 0.0,
        "time_mean": 0.0,
        "ip_address": "unknown",
    }