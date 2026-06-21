import React from "react";
import "./TopUsers.css";

import { mockUsageData } from "../../../../utils/client/mockUsageData";

const TopUsers = ({ users }) => {
  // 🔥 Fallback to mock
  const data = users?.length ? users : mockUsageData.top_users;

  if (!data || data.length === 0) {
    return <p className="usage-empty">No user activity data</p>;
  }

  return (
    <div className="top-users">
      {data.map((user, index) => (
        <div key={index} className="user-card">
          <div className="user-info">
            <span className="user-id">
              👤 {formatUser(user.user_id)}
            </span>
            <span className="user-requests">
              {user.requests} req
            </span>
          </div>

          <div className="user-bar">
            <div
              className="user-bar-fill"
              style={{
                width: `${getPercentage(data, user.requests)}%`
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

// 🔹 Format user id (clean UI)
const formatUser = (id) => {
  if (!id) return "anonymous";
  if (id.length <= 8) return id;
  return id.slice(0, 4) + "..." + id.slice(-3);
};

// 📊 Normalize percentage
const getPercentage = (data, value) => {
  const max = Math.max(...data.map((d) => d.requests));
  return max ? (value / max) * 100 : 0;
};

export default TopUsers;