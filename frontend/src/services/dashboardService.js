import api from './api';
import { generateMockStats, generateMockTrafficData, generateMockSuspiciousUsers, generateMockAlerts } from '../utils/mockData';

// Mock API calls - replace with real endpoints
export const dashboardService = {
  getStats: async () => {
    // Simulate API call
    return new Promise((resolve) => {
      setTimeout(() => resolve(generateMockStats()), 100);
    });
    // Real implementation:
    // return api.get('/dashboard/stats');
  },
  
  getTrafficData: async (timeframe = '15m') => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(generateMockTrafficData()), 100);
    });
    // return api.get(`/dashboard/traffic?timeframe=${timeframe}`);
  },
  
  getSuspiciousUsers: async () => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(generateMockSuspiciousUsers()), 100);
    });
    // return api.get('/dashboard/suspicious-users');
  },
  
  getRecentAlerts: async () => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(generateMockAlerts()), 100);
    });
    // return api.get('/dashboard/alerts');
  },
  
  getRiskScore: async (userId) => {
    return api.get(`/users/${userId}/risk`);
  },
  
  updatePolicy: async (policyData) => {
    return api.post('/policies/update', policyData);
  }
};