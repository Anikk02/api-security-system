// src/components/client/dashboard/RecentDecisions/RecentDecisions.jsx
import React from 'react';
import './RecentDecisions.css';
import { Check, Shield, X, Clock, AlertTriangle, Ban, FileText } from 'lucide-react';

const RecentDecisions = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="decisions-container">
        <div className="decisions-header">
          <h3 className="decisions-title">Recent Decisions</h3>
        </div>
        <div className="no-data">No recent decisions</div>
      </div>
    );
  }

  const getActionIcon = (action) => {
    const icons = {
      'block': <Ban size={14} />,
      'allow': <Check size={14} />,
      'throttle': <AlertTriangle size={14} />
    };
    return icons[action] || <FileText size={14} />;
  };

  const getActionClass = (action) => {
    const classes = {
      'block': 'blocked',
      'allow': 'allowed',
      'throttle': 'throttled'
    };
    return classes[action] || '';
  };

  const getActionLabel = (action) => {
    const labels = {
      'block': 'Blocked',
      'allow': 'Allowed',
      'throttle': 'Throttled'
    };
    return labels[action] || action;
  };

  const getTimeAgo = (timestamp) => {
    if (!timestamp) return 'Just now';
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const getReason = (log) => {
    if (log.explanation?.summary) return log.explanation.summary;
    if (log.explanation?.reason) return log.explanation.reason;
    return 'No reason provided';
  };

  return (
    <div className="decisions-container">
      <div className="decisions-header">
        <h3 className="decisions-title">Recent Decisions</h3>
        <button className="view-all-btn">View All</button>
      </div>
      <div className="decisions-list">
        {logs.slice(0, 8).map((log, index) => (
          <div key={log.id || index} className="decision-item">
            <div className="decision-icon">
              <span className={`icon-wrapper ${getActionClass(log.action)}`}>
                {getActionIcon(log.action)}
              </span>
            </div>
            <div className="decision-content">
              <div className="decision-row">
                <span className={`decision-action ${getActionClass(log.action)}`}>
                  {getActionLabel(log.action)}
                </span>
                <span className="decision-reason">{getReason(log)}</span>
              </div>
              <div className="decision-meta">
                {log.ip && <span className="decision-ip">{log.ip}</span>}
                {log.user && <span className="decision-user">{log.user}</span>}
                {log.endpoint && (
                  <>
                    <span className="decision-separator">•</span>
                    <span className="decision-endpoint">{log.endpoint}</span>
                  </>
                )}
                <span className="decision-separator">•</span>
                <span className="decision-time">{getTimeAgo(log.timestamp)}</span>
              </div>
            </div>
            <div className="decision-status">
              <span className={`status-dot ${getActionClass(log.action)}`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentDecisions;