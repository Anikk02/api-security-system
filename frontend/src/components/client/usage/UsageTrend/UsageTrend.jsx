import React from "react";
import "./UsageTrend.css";

import { mockUsageData } from "../../../../utils/client/mockUsageData";

const UsageTrend = ({ trend }) => {
  // 🔥 Fallback
  const data = trend?.length ? trend : mockUsageData.trend;

  if (!data || data.length === 0) {
    return <p className="usage-empty">No trend data available</p>;
  }

  // 📊 Normalize for chart height
  const max = Math.max(...data.map((d) => d.requests));

  return (
    <div className="usage-trend">
      <div className="trend-bars">
        {data.map((point, index) => {
          const height = max ? (point.requests / max) * 100 : 0;

          return (
            <div key={index} className="trend-bar-wrapper">
              <div
                className="trend-bar"
                style={{ height: `${height}%` }}
                title={`${point.requests} requests`}
              />
              <span className="trend-time">{point.time}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default UsageTrend;