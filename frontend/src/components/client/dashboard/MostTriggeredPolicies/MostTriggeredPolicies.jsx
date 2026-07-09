// src/components/client/dashboard/MostTriggeredPolicies/MostTriggeredPolicies.jsx
import React from 'react';
import './MostTriggeredPolicies.css';
import { AlertCircle, Shield, Zap, AlertTriangle, ArrowUp } from 'lucide-react';

const MostTriggeredPolicies = ({ policies }) => {
  const hasData = policies && Array.isArray(policies) && policies.length > 0;

  const getPolicyIcon = (name) => {
    if (name?.includes('Bot')) return <Zap size={16} />;
    if (name?.includes('Rate') || name?.includes('Burst')) return <AlertCircle size={16} />;
    if (name?.includes('Sensitive') || name?.includes('Scanning')) return <Shield size={16} />;
    return <AlertTriangle size={16} />;
  };

  const getSeverityColor = (name) => {
    if (name?.includes('Bot') || name?.includes('Scanning')) return '#ea4335';
    if (name?.includes('Rate') || name?.includes('Burst')) return '#fbbc04';
    return '#34a853';
  };

  return (
    <div className="policies-container">
      <h3 className="policies-title">Most Triggered Policies</h3>
      <div className="policies-content">
        {!hasData ? (
          <div className="no-data">No policy data available</div>
        ) : (
          <div className="policies-list">
            {policies.map((policy, index) => (
              <div key={index} className="policy-item">
                <div className="policy-header">
                  <div className="policy-name">
                    <span className="policy-icon" style={{ color: getSeverityColor(policy.name) }}>
                      {getPolicyIcon(policy.name)}
                    </span>
                    <span className="policy-label">{policy.name}</span>
                  </div>
                  <span className="policy-risk">
                    Risk: {policy.avgRiskScore?.toFixed(2) || 'N/A'}
                  </span>
                </div>
                <div className="policy-triggers">
                  {policy.triggerCount || 0} triggers ({policy.percentage || 0}%)
                </div>
                <div className="policy-stats">
                  <div className="stat-row">
                    <span className="stat-label allowed">Allowed</span>
                    <span className="stat-percentage allowed">
                      <ArrowUp size={10} strokeWidth={2.5} />
                      {policy.allowed || 0}%
                    </span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label blocked">Blocked</span>
                    <span className="stat-percentage blocked">
                      <ArrowUp size={10} strokeWidth={2.5} />
                      {policy.blocked || 0}%
                    </span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label throttled">Throttled</span>
                    <span className="stat-percentage throttled">
                      <ArrowUp size={10} strokeWidth={2.5} />
                      {policy.throttled || 0}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MostTriggeredPolicies;