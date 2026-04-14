import logging

logger = logging.getLogger(__name__)


class Explainer:
    """
    Generates explainable reasons for:
    - risk score
    - decision (allow / throttle / block)

    Output:
    {
        "summary": str,
        "factors": [str],
        "feature_contributions": dict
    }
    """

    @staticmethod
    def generate(action, reason, risk_score, features: dict, ml_data=None):
        try:
            factors = []
            contributions = {}

            # 1. BEHAVIORAL EXPLANATION
            req_count = features.get("request_count_60s", 0)
            burst = features.get("burst_ratio", 1.0)

            if req_count > 100:
                factors.append("High request volume detected")
                contributions["request_count_60s"] = req_count

            if burst > 3:
                factors.append("Abnormal traffic burst pattern")
                contributions["burst_ratio"] = burst

            # 2. PATTERN EXPLANATION
            entropy = features.get("endpoint_entropy", 0)
            repetition = features.get("repetition_score", 0)

            if entropy > 2.5:
                factors.append("Accessing many different endpoints (possible scanning)")
                contributions["endpoint_entropy"] = entropy

            if repetition > 0.8:
                factors.append("Highly repetitive requests (bot-like behavior)")
                contributions["repetition_score"] = repetition

            # 3. ERROR BASED SIGNALS
            error_rate = features.get("error_rate", 0)

            if error_rate > 0.5:
                factors.append("High error rate (possible probing or broken client)")
                contributions["error_rate"] = error_rate

            # 4. IDENTITY INSTABILITY
            ip_changes = features.get("ip_changes", 0)

            if ip_changes > 5:
                factors.append("Frequent IP changes detected")
                contributions["ip_changes"] = ip_changes

            # 5. USER AGENT ANALYSIS
            if features.get("is_bot"):
                factors.append("Request identified as bot traffic")

            if features.get("is_browser"):
                contributions["is_browser"] = 1

            # 6. TIMING PATTERNS
            time_variance = features.get("time_variance", 0)

            if time_variance < 0.01 and req_count > 20:
                factors.append("Highly regular request timing (automation suspected)")
                contributions["time_variance"] = time_variance

            # 7. ML CONTRIBUTION
            if ml_data:
                ml_reason = ml_data.get("reason")
                ml_score = ml_data.get("score")

                if ml_reason:
                    factors.append(f"ML model flagged: {ml_reason}")

                if ml_score is not None:
                    contributions["ml_score"] = ml_score

            # 8. FALLBACK
            if not factors:
                factors.append("No significant anomalies detected")

            # FINAL SUMMARY
            summary = Explainer._build_summary(action, risk_score, factors)

            return {
                "summary": summary,
                "factors": factors,
                "feature_contributions": contributions
            }

        except Exception as e:
            logger.error(f"Explainability failed: {e}")

            return {
                "summary": "Explanation unavailable",
                "factors": [],
                "feature_contributions": {}
            }

    # HELPER: Summary Builder
    @staticmethod
    def _build_summary(action, risk_score, factors):
        if action == "block":
            return f"Request blocked due to high risk (score={risk_score})"
        elif action == "throttle":
            return f"Request throttled due to suspicious behavior (score={risk_score})"
        else:
            return f"Request allowed (score={risk_score})"