// frontend/src/background/MetricsPanel.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/metrics.css';

const MetricsPanel = ({ metrics }) => {
  const metricItems = [
    { 
      label: 'Requests Processed', 
      value: metrics.requests.toLocaleString(), 
      change: '+12.5%',
      trend: 'up'
    },
    { 
      label: 'Blocked', 
      value: metrics.blocked.toLocaleString(), 
      change: '0.67%',
      trend: 'neutral'
    },
    { 
      label: 'Threats Detected', 
      value: metrics.threats.toLocaleString(), 
      change: `+${Math.floor(Math.random() * 5)}%`,
      trend: 'up'
    },
    { 
      label: 'Average Trust Score', 
      value: '82%', 
      change: '+2.3%',
      trend: 'up'
    }
  ];

  return (
    <div className="metrics-panel">
      {metricItems.map((metric, index) => (
        <motion.div 
          key={index}
          className="metric-item"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <div className="metric-label">{metric.label}</div>
          <div className="metric-value-wrapper">
            <span className="metric-value">{metric.value}</span>
            <span className={`metric-change ${metric.trend}`}>
              {metric.change}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default MetricsPanel;