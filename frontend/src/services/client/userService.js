import api from './api';

export const userService = {
  // (Assuming /api/users exists separately - keep as is if implemented)
  getUsers: async (params) => {
    const { page = 1, limit = 20, search = '' } = params;
    return await api.get('/api/users', {
      params: { page, limit, search }
    });
  },
  
  // ✅ FIXED: correct endpoint + mapping
  // Note: identityId is an opaque identity_id string (no "anon:"/"api:"
  // prefix anymore), not a numeric user id — encode it before it goes into a URL.
  getUserDetails: async (identityId) => {
    const response = await api.get(`/api/dashboard/user/${encodeURIComponent(identityId)}`);

    return {
      identityId: response.identity_id,
      isAnonymous: response.is_anonymous,
      totalRequests: response.total_requests,
      violations: response.violations,
      currentRiskScore: response.current_risk_score, // MAX risk (for display)
      avgRiskScore: response.avg_risk_score, // AVG risk (for trend)
      isBlocked: response.is_blocked,
      recentActions: response.recent_actions,
      ipHistory: response.ip_history
    };
  },
  
  // (Keep only if backend exists)
  getUserHistory: async (identityId, limit = 50) => {
    return await api.get(`/api/users/${encodeURIComponent(identityId)}/history`, {
      params: { limit }
    });
  },
  
  // ✅ FIXED: correct endpoint + query param
  blockUser: async (identityId, duration = 3600) => {
    return await api.post(`/api/dashboard/user/${encodeURIComponent(identityId)}/block`, null, {
      params: { duration }
    });
  },
  
  // ✅ FIXED: correct endpoint
  unblockUser: async (identityId) => {
    return await api.post(`/api/dashboard/user/${encodeURIComponent(identityId)}/unblock`);
  },

  sendWarning: async (identityId, message = 'Suspicious activity detected on your account') => {
    return await api.post(`/api/dashboard/user/${encodeURIComponent(identityId)}/warning`, null, {
      params: { message }
    });
  },
  
  // ❌ REMOVE (not implemented in backend)
  // updateUserWhitelist: async (userId, whitelist) => {
  //   return api.put(`/api/users/${userId}/whitelist`, { whitelist });
  // }
};