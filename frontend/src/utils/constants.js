export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

export const RISK_COLORS = {
  [RISK_LEVELS.LOW]: '#10b981',
  [RISK_LEVELS.MEDIUM]: '#f59e0b',
  [RISK_LEVELS.HIGH]: '#ef4444',
  [RISK_LEVELS.CRITICAL]: '#7f1d1d'
};

export const ACTIONS = {
  ALLOW: 'allow',
  THROTTLE: 'throttle',
  BLOCK: 'block'
};

export const CHART_CONFIG = {
  ANIMATION_DURATION: 300,
  TOOLTIP_STYLE: {
    backgroundColor: '#1e1e1e',
    border: '1px solid #2a2a2a',
    borderRadius: '8px',
    padding: '8px 12px'
  }
};

// Timeframes for traffic data
export const TIMEFRAMES = {
  FIFTEEN_MIN: '15m',
  ONE_HOUR: '1h',
  TWENTY_FOUR_HOUR: '24h'
};