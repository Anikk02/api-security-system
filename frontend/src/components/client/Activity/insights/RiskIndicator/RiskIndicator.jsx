import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./RiskIndicator.css";

function RiskIndicator({ trend }) {
  // ============================
  // 🧠 Fallback Logic
  // ============================
  const safeTrend =
    trend && trend.length > 0
      ? trend
      : mockActivityData.trend;

  if (!safeTrend || safeTrend.length === 0) return null;

  // ============================
  // 📊 Risk Calculation
  // ============================
  const latest = safeTrend[safeTrend.length - 1];

  const avg =
    safeTrend.reduce((sum, d) => sum + d.blocked, 0) /
    safeTrend.length;

  // Normalize risk score (0–100)
  const riskScore = Math.min(
    100,
    Math.round((latest.blocked / (avg * 2)) * 100)
  );

  let level = "low";
  if (riskScore > 75) level = "high";
  else if (riskScore > 40) level = "moderate";

  // ============================
  // 🎨 UI
  // ============================
  return (
    <div className="card risk-card">
      <h4>🧠 Risk Indicator</h4>

      <div className="risk-value">
        <span className={`risk-label ${level}`}>
          {level.toUpperCase()}
        </span>
        <span className="risk-score">{riskScore}%</span>
      </div>

      {/* Progress Bar */}
      <div className="risk-bar">
        <div
          className={`risk-fill ${level}`}
          style={{ width: `${riskScore}%` }}
        />
      </div>

      <p className="risk-sub">
        Based on anomaly vs average traffic
      </p>
    </div>
  );
}

export default RiskIndicator;