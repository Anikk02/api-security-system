// frontend/src/background/TrustGauge.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/gauges.css';

const TrustGauge = ({ value }) => {
  const getTrustColor = (val) => {
    if (val < 30) return '#e74c3c';
    if (val < 60) return '#e67e22';
    if (val < 80) return '#f1c40f';
    return '#2ecc71';
  };

  const getTrustLabel = (val) => {
    if (val < 30) return 'Untrusted';
    if (val < 60) return 'Suspicious';
    if (val < 80) return 'Trusted';
    return 'Verified';
  };

  return (
    <div className="gauge-wrapper trust-gauge">
      <div className="gauge-header">
        <span className="gauge-title">Trust Score</span>
        <span className="gauge-label" style={{ color: getTrustColor(value) }}>
          {getTrustLabel(value)}
        </span>
      </div>
      
      <div className="gauge-bar">
        <motion.div
          className="gauge-fill trust-fill"
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{
            background: `linear-gradient(90deg, ${getTrustColor(0)}, ${getTrustColor(value)})`
          }}
        />
      </div>
      
      <div className="gauge-value">
        <motion.span
          animate={{ scale: value < 30 ? [1, 1.2, 1] : 1 }}
          transition={{ duration: 0.3 }}
        >
          {value}%
        </motion.span>
      </div>
      
      <div className="gauge-steps">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>
    </div>
  );
};

export default TrustGauge;