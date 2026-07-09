// src/services/client/dashboardService.js
import api from './api';

// --- Stats ---
const mapStats = (data) => {
  const mappedData = {
    // For RiskMetricsOverview - Using 15-minute data
    avgRiskScore: data.avg_risk_score || 0,
    riskTrend: data.risk_trend || 0,
    activeUsers15m: data.active_users_15m || 0,
    activeUsersTrend: data.active_users_trend || 0,
    
    // Total Requests - using 15-minute data
    totalRequests: data.total_requests_15m || 0,
    totalRequestsTrend: data.total_requests_trend || 0,
    
    // Blocked - using 15-minute data
    blockedCount: data.blocked_count_15m || 0,
    blockedTrend: data.blocked_trend || 0,
    
    // Throttled - using 15-minute data
    throttledCount: data.throttled_count_15m || 0,
    throttledTrend: data.throttled_trend || 0,
    
    // Latency - using 15-minute data
    avgLatency: data.avg_latency || '0 ms',
    latencyTrend: data.latency_trend || 0,
    
    // Original fields (for StatsCards component - 1-minute data)
    requestsPerSecond: data.requests_per_second || 0,
    requestsTrend: data.requests_trend || 0,  // RPS trend (1-minute)
    violationsDetected: data.violations_detected || 0,
    violationsTrend: data.violations_trend || 0,
    suspiciousSessions: data.suspicious_sessions || 0,
    sessionsTrend: data.sessions_trend || 0,
    trafficComposition: {
      normal: data.traffic_composition?.normal || 0,
      suspicious: data.traffic_composition?.suspicious || 0,
      high_risk: data.traffic_composition?.high_risk || 0,
      critical: data.traffic_composition?.critical || 0
    },
    decisionsLastMin: data.decisions_last_min || { allowed: 0, throttled: 0, blocked: 0 }
  };
  
  return mappedData;
};

// --- TRAFFIC ---
const mapTrafficData = (response) => {
  // Handle both { data: [...] } and direct array responses
  const dataArray = response?.data || response || [];
  
  if (!Array.isArray(dataArray) || dataArray.length === 0) {
    return [];
  }
  
  return dataArray.map(point => ({
    time: new Date(point.time).getTime(),
    requests: point.requests || 0,
    anomalies: point.anomalies || 0,
    blocked: point.blocked || 0
  }));
};

// --- SUSPICIOUS USERS ---
const mapSuspiciousUser = (user) => ({
  id: user.identity_id || user.id,
  identityId: user.identity_id,
  violations: user.violations || 0,
  threatScore: user.threat_score || 0,
  status: user.status || 'low',
  ip: user.ip || 'unknown',
  lastSeen: user.last_seen ? new Date(user.last_seen) : new Date(),
  reason: user.reason || "No reason",
  isBlocked: user.is_blocked || false,
  account: user.identity_id
});

// --- ALERTS ---
const mapAlert = (alert) => ({
  id: alert.id,
  ip: alert.ip,
  score: alert.score,
  type: alert.type,
  timestamp: new Date(alert.timestamp),
  identityId: alert.identity_id
});

// --- LOGS ---
const mapLog = (log) => ({
  id: log.id,
  requestUuid: log.request_uuid,
  identityId: log.identity_id,
  endpoint: log.endpoint,
  ip: log.ip_address,
  action: log.action,
  riskScore: log.risk_score,
  explanation: log.explanation || null,
  timestamp: new Date(log.created_at + 'Z'), // tells JS it's UTC
  user: log.identity_id ? `user_${log.identity_id.substring(0, 8)}` : null
});

export const dashboardService = {

  // --- STATS ---
  getStats: async () => {
    try {
      const response = await api.get('/api/dashboard/stats');
      return mapStats(response);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      throw error;
    }
  },

  // --- TRAFFIC ---
  getTrafficData: async (timeframe = '15m') => {
    try {
      const response = await api.get('/api/dashboard/traffic', {
        params: { timeframe }
      });
      return mapTrafficData(response);
    } catch (error) {
      console.error('Failed to fetch traffic data:', error);
      throw error;
    }
  },

  // --- SUSPICIOUS USERS ---
  getSuspiciousUsers: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/suspicious-users', {
        params: { limit }
      });
      return (response || []).map(mapSuspiciousUser);
    } catch (error) {
      console.error('Failed to fetch suspicious users:', error);
      throw error;
    }
  },

  // --- ALERTS ---
  getRecentAlerts: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/alerts', {
        params: { limit }
      });
      return (response || []).map(mapAlert);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      throw error;
    }
  },

  // --- LOGS ---
  getDecisionLogs: async (page = 1, limit = 20) => {
    try {
      const response = await api.get('/api/dashboard/logs', {
        params: { page, limit }
      });
      return (response || []).map(mapLog);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      throw error;
    }
  },

  // --- IP TREND ---
  getIpTrend: async (ip) => {
    try {
      const response = await api.get(`/api/dashboard/ip/${encodeURIComponent(ip)}/trend`);
      return (response || []).map(p => ({
        time: new Date(p.time).getTime(),
        risk: p.risk
      }));
    } catch (error) {
      console.error('Failed to fetch IP trend:', error);
      throw error;
    }
  },

  // --- USER DETAILS ---
  getUserDetails: async (userId, clientId = null) => {
    try {
      const params = clientId ? { client_id: clientId } : {};
      const response = await api.get(`/api/dashboard/user/${encodeURIComponent(userId)}`, {
        params
      });
      return {
        identityId: response.identity_id,
        clientId: response.client_id,
        isAnonymous: response.is_anonymous,
        totalRequests: response.total_requests,
        violations: response.violations,
        currentRiskScore: response.current_risk_score,
        avgRiskScore: response.avg_risk_score,
        isBlocked: response.is_blocked,
        recentActions: response.recent_actions,
        ipHistory: response.ip_history
      };
    } catch (error) {
      console.error('Failed to fetch user details:', error);
      throw error;
    }
  },

  // --- BLOCK USER ---
  blockUser: async (userId, duration = 3600, clientId = null) => {
    try {
      const params = { duration };
      if (clientId) params.client_id = clientId;
      const response = await api.post(`/api/dashboard/user/${encodeURIComponent(userId)}/block`, null, {
        params
      });
      return response;
    } catch (error) {
      console.error('Failed to block user:', error);
      throw error;
    }
  },

  // --- UNBLOCK USER ---
  unblockUser: async (userId, clientId = null) => {
    try {
      const params = {};
      if (clientId) params.client_id = clientId;
      const response = await api.post(`/api/dashboard/user/${encodeURIComponent(userId)}/unblock`, null, {
        params
      });
      return response;
    } catch (error) {
      console.error('Failed to unblock user:', error);
      throw error;
    }
  },

  // 🔥 NEW: TOP POLICIES
  getTopPolicies: async (limit = 5) => {
    try {
      const response = await api.get('/api/dashboard/top-policies', {
        params: { limit }
      });
      return response.map(policy => ({
        name: policy.name,
        triggerCount: policy.trigger_count,
        percentage: policy.percentage,
        avgRiskScore: policy.avg_risk_score,
        allowed: policy.allowed || 0,
        blocked: policy.blocked || 0,
        throttled: policy.throttled || 0,
      }));
    } catch (error) {
      console.error('Failed to fetch top policies:', error);
      throw error;
    }
  }
};