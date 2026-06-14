import React from "react";
import { useNavigate } from "react-router-dom";
import "./EndpointDistribution.css";

function EndpointDistribution({ data = [] }) {
  const navigate = useNavigate();

  if (!data.length) {
    return (
      <div className="endpoint-card">
        <h2 className="endpoint-title">🎯 Endpoint Hotspots</h2>
        <p className="endpoint-empty">No endpoint activity available</p>
      </div>
    );
  }

  // 🧠 Find most targeted endpoint
  const maxRequests = Math.max(...data.map(d => d.requests));

  const handleClick = (endpoint) => {
    // 🎯 Navigate to logs with filter
    navigate(`/logs?endpoint=${encodeURIComponent(endpoint)}`);
  };

  return (
    <div className="endpoint-card">
      <h2 className="endpoint-title">🎯 Endpoint Hotspots</h2>

      <div className="endpoint-list">
        {data.map((item, index) => {
          const isTop = item.requests === maxRequests;

          return (
            <div
              key={index}
              className="endpoint-row"
              onClick={() => handleClick(item.endpoint)}
            >
              {/* Header */}
              <div className="endpoint-header">
                <div className="endpoint-left">
                  <span className="endpoint-name">{item.endpoint}</span>

                  {isTop && (
                    <span className="badge top-badge">
                      MOST TARGETED
                    </span>
                  )}
                </div>

                <div className="endpoint-right">
                  <span className="endpoint-percent">
                    {item.percentage}%
                  </span>
                  <span className="endpoint-count">
                    {item.requests} req
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="endpoint-bar">
                <div
                  className={`endpoint-fill ${getSeverityClass(item)}`}
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default EndpointDistribution;

//
// 🧠 Severity Logic
//
function getSeverityClass(item) {
  if (item.percentage > 60) return "critical";
  if (item.percentage > 40) return "high";
  if (item.percentage > 20) return "medium";
  return "low";
}