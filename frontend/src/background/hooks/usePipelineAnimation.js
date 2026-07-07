// frontend/src/background/hooks/usePipelineAnimation.js
import { useState, useCallback } from 'react';

export const usePipelineAnimation = () => {
  const [pipelineState, setPipelineState] = useState({
    identity: false,
    featureBuilder: false,
    riskEngine: false,
    trustEngine: false,
    policyEngine: false,
    penaltyManager: false
  });

  const triggerPipeline = useCallback((packet) => {
    // Reset all states
    setPipelineState({
      identity: false,
      featureBuilder: false,
      riskEngine: false,
      trustEngine: false,
      policyEngine: false,
      penaltyManager: false
    });

    // Simulate sequential pipeline processing
    const stages = [
      'identity',
      'featureBuilder',
      'riskEngine',
      'trustEngine',
      'policyEngine',
      'penaltyManager'
    ];

    stages.forEach((stage, index) => {
      setTimeout(() => {
        setPipelineState(prev => ({ ...prev, [stage]: true }));
      }, (index + 1) * 500);
    });

    // Reset after pipeline completes
    setTimeout(() => {
      setPipelineState({
        identity: false,
        featureBuilder: false,
        riskEngine: false,
        trustEngine: false,
        policyEngine: false,
        penaltyManager: false
      });
    }, stages.length * 500 + 1000);
  }, []);

  return { pipelineState, triggerPipeline };
};