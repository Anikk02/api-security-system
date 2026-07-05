// frontend/src/background/PipelineNode.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/nodes.css';

const PipelineNode = ({ id, label, x, y, isActive }) => {
  const getIcon = () => {
    const icons = {
      identity: '🛡️',
      featureBuilder: '⚡',
      riskEngine: '📊',
      trustEngine: '🔒',
      policyEngine: '📋',
      penaltyManager: '⚖️'
    };
    return icons[id] || '●';
  };

  return (
    <motion.div
      className={`pipeline-node ${isActive ? 'active' : ''}`}
      style={{
        position: 'absolute',
        left: `${x}%`,
        top: `${y}%`,
      }}
      animate={{
        scale: isActive ? 1.08 : 1,
        boxShadow: isActive ? '0 0 40px rgba(0, 255, 136, 0.2)' : 'none'
      }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <div className="node-content">
        <span className="node-icon">{getIcon()}</span>
        <span className="node-label">{label}</span>
      </div>
      
      {isActive && (
        <>
          <motion.div
            className="node-pulse"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.5, 0, 0.5]
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          />
          <motion.div
            className="node-ring"
            animate={{
              scale: [1, 1.5, 2],
              opacity: [0.3, 0.1, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeOut'
            }}
          />
        </>
      )}
    </motion.div>
  );
};

export default PipelineNode;