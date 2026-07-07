import React from "react";
import "./ApiKeyUsage.css";

import { mockUsageData } from "../../../../utils/client/mockUsageData";

const ApiKeyUsage = ({ apiKeys }) => {
  // 🔥 Fallback to mock data
  const data = apiKeys?.length ? apiKeys : mockUsageData.api_keys;

  if (!data || data.length === 0) {
    return <p className="usage-empty">No API key usage data</p>;
  }

  return (
    <div className="apikey-usage">
      {data.map((item, index) => (
        <div key={index} className="apikey-card">
          <div className="apikey-info">
            <span className="apikey-key">
              🔑 {maskKey(item.key)}
            </span>
            <span className="apikey-requests">
              {item.requests} req
            </span>
          </div>

          <div className="apikey-bar">
            <div
              className="apikey-bar-fill"
              style={{
                width: `${getPercentage(data, item.requests)}%`
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

// 🔐 Mask API key
const maskKey = (key) => {
  if (!key) return "unknown";
  return key.slice(0, 4) + "****" + key.slice(-4);
};

// 📊 Normalize percentage
const getPercentage = (data, value) => {
  const max = Math.max(...data.map((d) => d.requests));
  return max ? (value / max) * 100 : 0;
};

export default ApiKeyUsage;