import logging

logger = logging.getLogger(__name__)

class Explainer:
    """
    Generates explainable insights for:
    - Risk score
    - Final action (allow / throttle / block)

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

            # 1. RATE / VOLUME ANALYSIS
            req_per_min = features.get("req_per_min") or 0
            req_per_sec = features.get("req_per_sec") or 0

            if req_per_min > 100:
                factors.append("High request volume detected")
                contributions["req_per_min"] = req_per_min

            elif req_per_min > 50:
                factors.append("Moderately high request rate")
                contributions["req_per_min"] = req_per_min

            # 2. BURST BEHAVIOR
            burst_score = features.get("burst_score") or 0

            if burst_score > 0.7:
                factors.append("Abnormal traffic burst detected")
                contributions["burst_score"] = burst_score

            elif burst_score > 0.5:
                factors.append("Traffic burst pattern observed")
                contributions["burst_score"] = burst_score

            # 3. ENDPOINT PATTERNS
            entropy = features.get("endpoint_entropy") or 0
            unique_endpoints = features.get("unique_endpoints") or 0

            if entropy > 0.7:
                factors.append("High endpoint diversity (possible scanning)")
                contributions["endpoint_entropy"] = entropy

            elif entropy > 0.4:
                factors.append("Moderate endpoint variation")
                contributions["endpoint_entropy"] = entropy

            if unique_endpoints > 20:
                contributions["unique_endpoints"] = unique_endpoints

            # 4. ERROR BEHAVIOR
            error_rate = features.get("error_rate") or 0

            if error_rate > 0.5:
                factors.append("High error rate (possible probing or broken client)")
                contributions["error_rate"] = error_rate

            elif error_rate > 0.3:
                factors.append("Elevated error responses observed")
                contributions["error_rate"] = error_rate

            # 5. USER AGENT ANALYSIS
            if features.get("is_suspicious_ua"):
                factors.append("Suspicious or automated user agent detected")

            if features.get("is_bot"):
                factors.append("Bot-like traffic pattern identified")

            # 6. IDENTITY INSTABILITY
            ip_changes = features.get("ip_changes") or 0

            if ip_changes > 5:
                factors.append("Frequent IP changes detected")
                contributions["ip_changes"] = ip_changes

            # 7. TIME PATTERN ANALYSIS
            time_variance = features.get("time_variance") or 0
            regularity = features.get("request_regularity") or 0

            if time_variance < 0.02 and req_per_min > 20:
                factors.append("Highly regular request timing (automation suspected)")
                contributions["time_variance"] = time_variance

            if regularity > 0.8:
                factors.append("Consistent request intervals detected")
                contributions["request_regularity"] = regularity

            # 8. ML SIGNALS (FROM RISK ENGINE)
            if ml_data:
                label = ml_data.get("label")
                explanation = ml_data.get("explanation")
                contributions_ml = ml_data.get("contributions", {})

                if label == "high":
                    factors.append("ML model indicates high-risk behavior")
                elif label == "medium":
                    factors.append("ML model indicates suspicious activity")

                if explanation:
                    factors.append(f"ML insight: {explanation}")

                if contributions_ml:
                    contributions.update(contributions_ml)

            # 9. FALLBACK
            if not factors:
                factors.append("No significant anomalies detected")

            # FINAL SUMMARY
            summary = Explainer._build_summary(action, risk_score, reason)

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

    # SUMMARY BUILDER
    @staticmethod
    def _build_summary(action, risk_score, reason):
        if action == "block":
            return f"Request blocked due to high risk (score={risk_score}) - {reason}"

        elif action == "throttle":
            return f"Request throttled due to suspicious behavior (score={risk_score}) - {reason}"

        else:
            return f"Request allowed (score={risk_score}) - {reason}"

