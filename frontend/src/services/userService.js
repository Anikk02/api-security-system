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
  getUserDetails: async (userId) => {
    const response = await api.get(`/api/dashboard/user/${userId}`);

    return {
      userId: response.user_id,
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
  getUserHistory: async (userId, limit = 50) => {
    return await api.get(`/api/users/${userId}/history`, {
      params: { limit }
    });
  },
  
  // ✅ FIXED: correct endpoint + query param
  blockUser: async (userId, duration = 3600) => {
    return await api.post(`/api/dashboard/user/${userId}/block`, null, {
      params: { duration }
    });
  },
  
  // ✅ FIXED: correct endpoint
  unblockUser: async (userId) => {
    return await api.post(`/api/dashboard/user/${userId}/unblock`);
  },
  
  // ❌ REMOVE (not implemented in backend)
  // updateUserWhitelist: async (userId, whitelist) => {
  //   return api.put(`/api/users/${userId}/whitelist`, { whitelist });
  // }
};