import React from "react";
import mockActivityData from "../../../../../utils/client/mockActivityData";
import "./AttackPatterns.css";

function AttackPatterns({ endpoints }) {
  const safeEndpoints =
    endpoints && endpoints.length > 0
      ? endpoints
      : mockActivityData.endpoints;

  if (!safeEndpoints.length) return null;

  // 🔥 Detect repeated attack targets (>20%)
  const patterns = safeEndpoints.filter((e) => e.percentage > 20);

  return (
    <div className="card attack-patterns">
      <h3>🧠 Attack Patterns</h3>

      {patterns.length === 0 ? (
        <p className="no-patterns">No strong patterns detected</p>
      ) : (
        <div className="patterns-list">
          {patterns.map((p, i) => (
            <div key={i} className="pattern-item">
              <span className="endpoint">{p.endpoint}</span>
              <span className="percentage">{p.percentage}%</span>
            </div>
          ))}
        </div>
      )}

      <p className="pattern-sub">
        Repeated targeting based on endpoint distribution
      </p>
    </div>
  );
}

export default AttackPatterns;