import api from './api';

// --- Stats ---
const mapStats = (data) => ({
  requestsPerSecond: data.requests_per_second,
  requestsTrend: data.requests_trend,
  violationsDetected: data.violations_detected,
  violationsTrend: data.violations_trend,
  suspiciousSessions: data.suspicious_sessions,
  sessionsTrend: data.sessions_trend,
  trafficComposition: data.traffic_composition
});

// --- Traffic ---
const mapTrafficData = (response) => {
  return response.data.map(point => ({
    time: new Date(point.time).getTime(),
    requests: point.requests,
    anomalies: point.anomalies,
    blocked: point.blocked
  }));
};

// --- Suspicious Users ---
const mapSuspiciousUser = (user) => ({
  id: user.id,
  violations: user.violations,
  threatScore: user.threat_score,
  status: user.status,
  ip: user.ip,
  lastSeen: new Date(user.last_seen),
  reason: user.reason || "No reason",
  isBlocked: user.is_blocked || false
});

// --- Alerts ---
const mapAlert = (alert) => ({
  id: alert.id,
  ip: alert.ip,
  score: alert.score,
  type: alert.type,
  timestamp: new Date(alert.timestamp),
  identityId: alert.identity_id // opaque identity_id string, not a numeric user id
});

// --- Logs ---
const mapLog = (log) => ({
  id: log.id,
  requestUuid: log.request_uuid,
  identityId: log.identity_id, // opaque identity_id string, not a numeric user id
  endpoint: log.endpoint,
  ip: log.ip_address,
  action: log.action,
  riskScore: log.risk_score,
  explanation: log.explanation || null,
  timestamp: new Date(log.created_at)
});

export const dashboardService = {

  // --- STATS ---
  getStats: async () => {
    try {
      const response = await api.get('/api/dashboard/stats');
      return mapStats(response);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      return {
        requestsPerSecond: 0,
        requestsTrend: 0,
        violationsDetected: 0,
        violationsTrend: 0,
        suspiciousSessions: 0,
        sessionsTrend: 0,
        trafficComposition: { normal: 0, suspicious: 0, high_risk: 0 }
      };
    }
  },

  // --- TRAFFIC ---
  getTrafficData: async (timeframe = '15m') => {
    try {
      const response = await api.get('/api/dashboard/traffic', {
        params: { timeframe }
      });
      return mapTrafficData(response); // response.data already handled
    } catch (error) {
      console.error('Failed to fetch traffic data:', error);
      return [];
    }
  },

  // --- SUSPICIOUS USERS ---
  getSuspiciousUsers: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/suspicious-users', {
        params: { limit }
      });
      return response.map(mapSuspiciousUser);
    } catch (error) {
      console.error('Failed to fetch suspicious users:', error);
      return [];
    }
  },

  // --- ALERTS ---
  getRecentAlerts: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/alerts', {
        params: { limit }
      });
      return response.map(mapAlert);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      return [];
    }
  },

  // --- LOGS ---
  getDecisionLogs: async (page = 1, limit = 20) => {
    try {
      const response = await api.get('/api/dashboard/logs', {
        params: { page, limit }
      });
      return response.map(mapLog);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      return [];
    }
  },

  getIpTrend: async (ip) => {
    const response = await api.get(`/api/dashboard/ip/${encodeURIComponent(ip)}/trend`);
    return response.map(p => ({
      time: new Date(p.time).getTime(),
      risk: p.risk
    }))
  }
};