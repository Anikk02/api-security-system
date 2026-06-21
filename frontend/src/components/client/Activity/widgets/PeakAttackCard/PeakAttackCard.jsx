import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./PeakAttackCard.css";

function PeakAttackCard({ trend }) {
  // ============================
  // 🧠 Fallback Logic
  // ============================
  const safeTrend =
    trend && trend.length > 0
      ? trend
      : mockActivityData.trend;

  if (!safeTrend || safeTrend.length === 0) return null;

  // ============================
  // 📊 Compute Peak Attack
  // ============================
  const peak = safeTrend.reduce((a, b) =>
    a.blocked > b.blocked ? a : b
  );

  const avg =
    safeTrend.reduce((sum, d) => sum + d.blocked, 0) /
    safeTrend.length;

  const isSevere = peak.blocked > avg * 2;

  // ============================
  // 🎨 UI
  // ============================
  return (
    <div className={`card peak-card ${isSevere ? "severe" : ""}`}>
      <h4>📈 Peak Attack</h4>

      <div className="peak-value">
        <span className="peak-time">{peak.time}</span>
        <span className="peak-count">{peak.blocked}</span>
      </div>

      <div className="peak-meta">
        <span>Blocked Requests</span>
        {isSevere && (
          <span className="peak-badge">🚨 Severe</span>
        )}
      </div>

      <p className="peak-sub">
        Highest blocked traffic observed in timeframe
      </p>
    </div>
  );
}

export default PeakAttackCard;