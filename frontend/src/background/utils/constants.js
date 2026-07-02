// frontend/src/background/utils/constants.js
export const PIPELINE_STAGES = [
  'identity',
  'featureBuilder',
  'riskEngine',
  'trustEngine',
  'policyEngine',
  'penaltyManager'
];

export const STAGE_LABELS = {
  identity: 'Identity Engine',
  featureBuilder: 'Feature Builder',
  riskEngine: 'Risk Engine',
  trustEngine: 'Trust Engine',
  policyEngine: 'Policy Engine',
  penaltyManager: 'Penalty Manager'
};

export const STAGE_ICONS = {
  identity: '🛡️',
  featureBuilder: '⚡',
  riskEngine: '📊',
  trustEngine: '🔒',
  policyEngine: '📋',
  penaltyManager: '⚖️'
};

export const METHOD_COLORS = {
  GET: '#3498db',
  POST: '#2ecc71',
  PUT: '#f1c40f',
  DELETE: '#e74c3c'
};

export const STATUS_COLORS = {
  Allowed: '#2ecc71',
  Blocked: '#e74c3c',
  Challenge: '#f1c40f'
};

export const PENALTY_LEVELS = {
  0: 'No Penalty',
  1: 'Rate Limit',
  2: 'Temporary Ban',
  3: 'IP Block',
  4: 'Permanent Ban'
};