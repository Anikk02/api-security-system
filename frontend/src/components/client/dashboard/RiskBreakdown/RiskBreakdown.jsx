// src/components/client/dashboard/RiskBreakdown/RiskBreakdown.jsx
import React from 'react';
import './RiskBreakdown.css';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const RiskBreakdown = ({ data }) => {
  // Check if data exists and has values
  const hasData = data && Array.isArray(data) && data.length > 0 && data.some(item => item.value > 0);

  const total = hasData ? data.reduce((sum, item) => sum + item.value, 0) : 0;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      const percentage = total > 0 ? ((dataPoint.value / total) * 100).toFixed(1) : 0;
      return (
        <div className="tooltip">
          <span className="tooltip-name">{dataPoint.name}</span>
          <span className="tooltip-value">
            {dataPoint.value.toLocaleString()} ({percentage}%)
          </span>
        </div>
      );
    }
    return null;
  };

  const renderLegend = () => {
    if (!hasData) return null;
    
    return (
      <div className="legend-container">
        {data.map((entry, index) => {
          const percentage = total > 0 ? ((entry.value / total) * 100).toFixed(1) : 0;
          return (
            <div key={`legend-${index}`} className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: entry.color }} />
              <span className="legend-label">{entry.name}</span>
              <span className="legend-value">{percentage}%</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="risk-breakdown-container">
      <h3 className="risk-title">Risk Breakdown</h3>
      {!hasData ? (
        <div className="no-data">No risk data available</div>
      ) : (
        <div className="risk-content">
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="risk-summary">
            {renderLegend()}
            <div className="summary-divider" />
            <div className="summary-total">
              <span className="summary-label">Total Requests</span>
              <span className="summary-value">{total.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskBreakdown;