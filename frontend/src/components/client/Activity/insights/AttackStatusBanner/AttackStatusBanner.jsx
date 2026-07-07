import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./AttackStatusBanner.css";

function AttackStatusBanner({ trend }) {
  // ============================
  // 🧠 Fallback Logic
  // ============================
  const safeTrend =
    trend && trend.length > 0
      ? trend
      : mockActivityData.trend;

  if (!safeTrend || safeTrend.length === 0) return null;

  // ============================
  // 📊 Anomaly Detection
  // ============================
  const latest = safeTrend[safeTrend.length - 1];

  const avg =
    safeTrend.reduce((sum, d) => sum + d.blocked, 0) /
    safeTrend.length;

  const isAttack = latest.blocked > avg * 2;
  const isWarning = latest.blocked > avg;

  // ============================
  // 🎯 Status Config
  // ============================
  let status = "normal";
  let message = "System Stable";
  let icon = "✅";

  if (isAttack) {
    status = "attack";
    message = "Attack Spike Detected";
    icon = "🚨";
  } else if (isWarning) {
    status = "warning";
    message = "Unusual Activity Detected";
    icon = "⚠️";
  }

  // ============================
  // 🎨 UI
  // ============================
  return (
    <div className={`attack-banner ${status}`}>
      <div className="banner-content">
        <span className="banner-icon">{icon}</span>

        <div>
          <p className="banner-title">{message}</p>
          <span className="banner-sub">
            {latest.blocked} blocked requests (avg {Math.round(avg)})
          </span>
        </div>
      </div>
    </div>
  );
}

export default AttackStatusBanner;