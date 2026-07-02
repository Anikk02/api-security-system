// frontend/src/background/data/pipeline.js
export const pipelineStages = [
  { id: 'identity', label: 'Identity Engine', icon: '🛡️' },
  { id: 'featureBuilder', label: 'Feature Builder', icon: '⚡' },
  { id: 'riskEngine', label: 'Risk Engine', icon: '📊' },
  { id: 'trustEngine', label: 'Trust Engine', icon: '🔒' },
  { id: 'policyEngine', label: 'Policy Engine', icon: '📋' },
  { id: 'penaltyManager', label: 'Penalty Manager', icon: '⚖️' }
];

export const pipelineConnections = [
  { from: 'identity', to: 'featureBuilder' },
  { from: 'featureBuilder', to: 'riskEngine' },
  { from: 'riskEngine', to: 'trustEngine' },
  { from: 'trustEngine', to: 'policyEngine' },
  { from: 'policyEngine', to: 'penaltyManager' }
];