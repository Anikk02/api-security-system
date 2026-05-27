import api from './api';

export const userService = {
  getUsers: async (params) => {
    return api.get('/users', { params });
  },
  
  getUserDetails: async (userId) => {
    return api.get(`/users/${userId}`);
  },
  
  getUserHistory: async (userId) => {
    return api.get(`/users/${userId}/history`);
  },
  
  blockUser: async (userId, duration) => {
    return api.post(`/users/${userId}/block`, { duration });
  },
  
  unblockUser: async (userId) => {
    return api.post(`/users/${userId}/unblock`);
  },
  
  updateUserWhitelist: async (userId, whitelist) => {
    return api.put(`/users/${userId}/whitelist`, { whitelist });
  }
};