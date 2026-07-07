import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./SystemHealthCard.css";

function SystemHealthCard({ trend }) {
  // ============================
  // 🧠 Fallback Logic
  // ============================
  const safeTrend =
    trend && trend.length > 0
      ? trend
      : mockActivityData.trend;

  if (!safeTrend || safeTrend.length === 0) return null;

  // ============================
  // 📊 Health Calculation
  // ============================
  let total = 0;
  let blocked = 0;

  safeTrend.forEach((d) => {
    total += d.total || (d.allowed + d.blocked);
    blocked += d.blocked;
  });

  const success = total - blocked;

  // Health score = allowed traffic ratio
  const healthScore = total > 0
    ? Math.round((success / total) * 100)
    : 100;

  // ============================
  // 🧠 Health Status
  // ============================
  let status = "healthy";
  let label = "Healthy";
  let icon = "🟢";

  if (healthScore < 70) {
    status = "critical";
    label = "Critical";
    icon = "🔴";
  } else if (healthScore < 90) {
    status = "degraded";
    label = "Degraded";
    icon = "🟡";
  }

  // ============================
  // 🎨 UI
  // ============================
  return (
    <div className={`card health-card ${status}`}>
      <h4>🛡️ System Health</h4>

      <div className="health-header">
        <span className="health-icon">{icon}</span>
        <span className="health-label">{label}</span>
      </div>

      <div className="health-score">
        {healthScore}%
      </div>

      <div className="health-bar">
        <div
          className={`health-fill ${status}`}
          style={{ width: `${healthScore}%` }}
        />
      </div>

      <div className="health-meta">
        <span>Allowed: {success}</span>
        <span>Blocked: {blocked}</span>
      </div>

      <p className="health-sub">
        Based on traffic success vs blocked ratio
      </p>
    </div>
  );
}

export default SystemHealthCard;