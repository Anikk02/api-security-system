import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./ActivityInsights.css";

function ActivityInsights({ endpoints, trend }) {
  // ============================
  // 🧠 Fallback Logic (CRITICAL)
  // ============================
  const safeEndpoints =
    endpoints && endpoints.length > 0
      ? endpoints
      : mockActivityData.endpoints;

  const safeTrend =
    trend && trend.length > 0
      ? trend
      : mockActivityData.trend;

  // ============================
  // 📊 Derived Intelligence
  // ============================

  const topEndpoint = safeEndpoints.reduce((a, b) =>
    a.requests > b.requests ? a : b
  );

  const peakAttack = safeTrend.reduce((a, b) =>
    a.blocked > b.blocked ? a : b
  );

  const avgBlocked =
    safeTrend.reduce((sum, d) => sum + d.blocked, 0) /
    safeTrend.length;

  const riskLevel =
    peakAttack.blocked > avgBlocked * 2
      ? "High"
      : peakAttack.blocked > avgBlocked
      ? "Moderate"
      : "Low";

  // ============================
  // 🎨 UI
  // ============================

  return (
    <div className="insights-row">
      {/* 🎯 Most Targeted */}
      <div className="card insight-card">
        <h4>🎯 Most Targeted Endpoint</h4>
        <p className="insight-value">{topEndpoint.endpoint}</p>
        <span className="insight-sub">
          {topEndpoint.requests} requests
        </span>
      </div>

      {/* 📈 Peak Attack */}
      <div className="card insight-card">
        <h4>📈 Peak Attack Time</h4>
        <p className="insight-value">{peakAttack.time}</p>
        <span className="insight-sub">
          {peakAttack.blocked} blocked
        </span>
      </div>

      {/* ⚠️ Risk Level */}
      <div className={`card insight-card risk-${riskLevel.toLowerCase()}`}>
        <h4>⚠️ Risk Level</h4>
        <p className="insight-value">{riskLevel}</p>
        <span className="insight-sub">
          Based on anomaly detection
        </span>
      </div>
    </div>
  );
}

export default ActivityInsights;