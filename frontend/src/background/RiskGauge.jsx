// frontend/src/background/RiskGauge.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/gauges.css';

const RiskGauge = ({ value }) => {
  const getRiskColor = (val) => {
    if (val < 30) return '#2ecc71';
    if (val < 60) return '#f1c40f';
    if (val < 80) return '#e67e22';
    return '#e74c3c';
  };

  const getRiskLabel = (val) => {
    if (val < 30) return 'Low';
    if (val < 60) return 'Medium';
    if (val < 80) return 'High';
    return 'Critical';
  };

  return (
    <div className="gauge-wrapper risk-gauge">
      <div className="gauge-header">
        <span className="gauge-title">Risk Score</span>
        <span className="gauge-label" style={{ color: getRiskColor(value) }}>
          {getRiskLabel(value)}
        </span>
      </div>
      
      <div className="gauge-bar">
        <motion.div
          className="gauge-fill risk-fill"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{
            background: `linear-gradient(90deg, ${getRiskColor(0)}, ${getRiskColor(value)})`
          }}
        />
        <motion.div
          className="gauge-needle"
          animate={{
            rotate: `-${90 - (value / 100) * 180}deg`
          }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
      
      <div className="gauge-value">
        <motion.span
          animate={{ scale: value > 70 ? [1, 1.2, 1] : 1 }}
          transition={{ duration: 0.3 }}
        >
          {value}%
        </motion.span>
      </div>
    </div>
  );
};

export default RiskGauge;