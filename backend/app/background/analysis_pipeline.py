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
):
    try:

        # -------------------------------------------------------
        # Track Errors
        # -------------------------------------------------------

        if status_code is not None and status_code >= 400:
            await StateManager.increment_error(identity)

        await StateManager.record_outcome(
            identity=identity,
            endpoint=signals.endpoint,
            status_code=status_code or 200,
        )

        # -------------------------------------------------------
        # Build Features
        # -------------------------------------------------------

        try:
            features = await _get_feature_builder().build(
                identity,
                signals,
            )

        except Exception as e:

            logger.exception(
                f"[pipeline] FeatureBuilder failed : {e}"
            )

            features = _empty_features()

        # -------------------------------------------------------
        # Compute Risk
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

            logger.exception(
                f"[pipeline] RiskEngine failed : {e}"
            )

            risk_score = fast_risk_score

            risk_data = {
                "label": "low",
                "explanation": "fallback",
                "contributions": {},
            }

        # -------------------------------------------------------
        # Penalty Manager
        # -------------------------------------------------------

        try:

            decision: PenaltyDecision = await apply_penalty(
                identity=identity,
                signals=signals,
                risk_score=risk_score,
            )

        except Exception as e:

            logger.exception(
                f"[pipeline] PenaltyManager failed : {e}"
            )

            decision = PenaltyDecision(
                action="allow",
                reason="Penalty fallback",
                risk_score=risk_score,
                trust_score=1.0,
                reputation=0.0,
            )

        # -------------------------------------------------------
        # Explainability
        # -------------------------------------------------------

        explanation_json = Explainer.generate(
            action=decision.action,
            reason=decision.reason,
            risk_score=risk_score,
            features=features,
            risk_data=risk_data,      # rename later if desired
        )

        # -------------------------------------------------------
        # DB Logging
        # -------------------------------------------------------

        await _log_to_db(
            identity=identity,
            signals=signals,
            features=features,
            decision=decision,
            risk_score=risk_score,
            risk_data=risk_data,
            explanation=explanation_json,
            request_uuid=request_uuid,
            status_code=status_code or 200,
            label=label,
        )

        logger.debug(
            "[pipeline] "
            f"identity={identity.identity_id} | "
            f"risk={risk_score:.3f} | "
            f"trust={decision.trust_score:.3f} | "
            f"rep={decision.reputation:.3f} | "
            f"action={decision.action}"
        )

    except Exception:

        logger.exception(
            f"[pipeline] Unhandled exception "
            f"identity={identity.identity_id}"
        )


async def _log_to_db(
    *,
    identity,
    signals,
    features,
    decision: PenaltyDecision,
    risk_score,
    risk_data,
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
                action=decision.action,
                request_uuid=request_uuid,
            )

            db.add(request_log)

            await db.flush()

            request_id = request_log.id

            db.add(
                DecisionLog(
                    identity_id=identity.identity_id,
                    client_id=identity.client_id,
                    api_key_id=api_key_id,
                    request_id=request_id,
                    action=decision.action,
                    reason=decision.reason,
                    risk_score=risk_score,
                    explanation=explanation.get("summary"),
                    explanation_json=explanation,
                    ground_truth_label=label,
                    request_uuid=request_uuid,
                )
            )

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
                        feature_contributions=explanation.get(
                            "feature_contributions"
                        ),
                        request_uuid=request_uuid,
                    )
                )

            await db.commit()

    except Exception as e:

        logger.exception(
            f"[pipeline] DB logging failed : {e}"
        )


def _empty_features() -> dict:
    return {
        # Request metrics
        "req_per_sec": 0.0,
        "req_per_min": 0.0,
        "burst_score": 0.0,

        # Endpoint behaviour
        "unique_endpoints": 0,
        "endpoint_entropy": 0.0,
        "top_endpoint_ratio": 0.0,

        # Error / rate limiting
        "error_rate": 0.0,
        "is_rate_limited": False,

        # Identity
        "ip_changes": 0,
        "is_bot": False,
        "is_browser": False,
        "is_suspicious_ua": False,

        # Timing
        "request_regularity": 0.0,
        "time_variance": 0.0,
        "time_mean": 0.0,

        # Optional values used by FeatureLog
        "ip_address": "unknown",
    }