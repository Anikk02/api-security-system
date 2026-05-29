import api from './api';

export const userService = {
  getUsers: async (params) => {
    const { page = 1, limit = 20, search = '' } = params;
    const response = await api.get('/api/users', {
      params: { page, limit, search }
    });
    return response;
  },
  
  getUserDetails: async (userId) => {
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
  },
  
  getUserHistory: async (userId, limit = 50) => {
    const response = await api.get(`/api/users/${userId}/history`, {
      params: { limit }
    });
    return response;
  },
  
  blockUser: async (userId, duration) => {
    return api.post(`/api/users/${userId}/block`, { duration });
  },
  
  unblockUser: async (userId) => {
    return api.post(`/api/users/${userId}/unblock`);
  },
  
  updateUserWhitelist: async (userId, whitelist) => {
    return api.put(`/api/users/${userId}/whitelist`, { whitelist });
  }
};