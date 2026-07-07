import React from "react";
import "./PeakUsageTime.css";

import { mockUsageData } from "../../../../utils/client/mockUsageData";

const PeakUsageTime = ({ trend }) => {
  // 🔥 Fallback to mock
  const data = trend?.length ? trend : mockUsageData.trend;

  if (!data || data.length === 0) {
    return <p className="usage-empty">No usage trend data</p>;
  }

  // 📊 Find peak
  const peak = data.reduce((max, curr) =>
    curr.requests > max.requests ? curr : max
  );

  return (
    <div className="peak-usage">
      <div className="peak-time">
        ⏱ {peak.time}
      </div>

      <div className="peak-requests">
        {peak.requests} requests
      </div>

      <p className="peak-desc">
        Highest API usage observed during this period
      </p>
    </div>
  );
};

export default PeakUsageTime;