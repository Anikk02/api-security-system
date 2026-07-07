// frontend/src/background/DecisionNode.jsx
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/nodes.css';

const DecisionNode = ({ pipelineState }) => {
  const decisions = ['Allow', 'Throttled', 'Block'];
  const [currentDecision, setCurrentDecision] = React.useState('Allow');

  React.useEffect(() => {
    if (pipelineState.policyEngine) {
      const random = Math.random();
      if (random < 0.6) setCurrentDecision('Allow');
      else if (random < 0.85) setCurrentDecision('Throttled');
      else setCurrentDecision('Block');
    }
  }, [pipelineState.policyEngine]);

  const getDecisionColor = (decision) => {
    const colors = {
      Allow: '#2ecc71',
      Throttled: '#f1c40f',
      Block: '#e74c3c'
    };
    return colors[decision] || '#00ff88';
  };

  return (
    <motion.div 
      className="decision-node"
      animate={{
        scale: pipelineState.policyEngine ? 1.05 : 1,
        opacity: pipelineState.policyEngine ? 1 : 0.5
      }}
      transition={{ duration: 0.3 }}
    >
      <div className="decision-label">Decision</div>
      <motion.div
        className={`decision-value decision-${currentDecision.toLowerCase()}`}
        animate={{
          scale: pipelineState.policyEngine ? [1, 1.1, 1] : 1,
        }}
        transition={{
          duration: 0.5,
          repeat: pipelineState.policyEngine ? 1 : 0
        }}
        style={{
          color: getDecisionColor(currentDecision),
          borderColor: `${getDecisionColor(currentDecision)}44`
        }}
      >
        {currentDecision}
      </motion.div>
    </motion.div>
  );
};

export default DecisionNode;