import api from './api';

// Helper to convert backend snake_case to frontend camelCase
const mapStats = (data) => ({
  requestsPerSecond: data.requests_per_second,
  requestsTrend: data.requests_trend,
  violationsDetected: data.violations_detected,
  violationsTrend: data.violations_trend,
  suspiciousSessions: data.suspicious_sessions,
  sessionsTrend: data.sessions_trend,
  trafficComposition: data.traffic_composition
});

const mapTrafficData = (response) => {
  return response.data.map(point => ({
    time: new Date(point.time).getTime(),
    requests: point.requests,
    anomalies: point.anomalies,
    blocked: point.blocked
  }));
};

const mapSuspiciousUser = (user) => ({
  id: user.id,
  violations: user.violations,
  threatScore: user.threat_score,
  status: user.status,
  ip: user.ip,
  lastSeen: new Date(user.last_seen)
});

const mapAlert = (alert) => ({
  id: alert.id,
  ip: alert.ip,
  score: alert.score,
  type: alert.type,
  timestamp: new Date(alert.timestamp),
  userId: alert.user_id
});

const mapLog = (log) => ({
  id: log.id,
  requestUuid: log.request_uuid,
  userId: log.user_id,
  endpoint: log.endpoint,
  ip: log.ip_address,
  action: log.action,
  riskScore: log.risk_score,
  explanation: log.explanation,
  timestamp: new Date(log.created_at)
});

export const dashboardService = {
  // Get dashboard statistics
  getStats: async () => {
    try {
      const response = await api.get('/api/dashboard/stats');
      return mapStats(response);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Return mock data as fallback
      return {
        requestsPerSecond: 0,
        requestsTrend: 0,
        violationsDetected: 0,
        violationsTrend: 0,
        suspiciousSessions: 0,
        sessionsTrend: 0,
        trafficComposition: { normal: 0, bots: 0, suspicious: 0 }
      };
    }
  },
  
  // Get traffic data for charts
  getTrafficData: async (timeframe = '15m') => {
    try {
      const response = await api.get('/api/dashboard/traffic', {
        params: { timeframe }
      });
      return mapTrafficData(response);
    } catch (error) {
      console.error('Failed to fetch traffic data:', error);
      return [];
    }
  },
  
  // Get suspicious users list
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
  
  // Get recent alerts
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
  
  // Get decision logs with pagination
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
  
  // Get total count of logs (for pagination)
  getLogsCount: async () => {
    try {
      const response = await api.get('/api/dashboard/logs/count');
      return response.count || 0;
    } catch (error) {
      console.error('Failed to fetch logs count:', error);
      return 0;
    }
  },
  
  // Get user details
  getUserDetails: async (userId) => {
    try {
      const response = await api.get(`/api/dashboard/user/${userId}`);
      return {
        userId: response.user_id,
        isAnonymous: response.is_anonymous,
        totalRequests: response.total_requests,
        violations: response.violations,
        currentRiskScore: response.current_risk_score,
        isBlocked: response.is_blocked,
        recentActions: response.recent_actions,
        ipHistory: response.ip_history
      };
    } catch (error) {
      console.error('Failed to fetch user details:', error);
      return null;
    }
  }
};