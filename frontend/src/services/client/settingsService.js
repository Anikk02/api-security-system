import api from './api';

export const getSettingsOverview = async () => {
  return await api.get('/api/settings/overview');
};

export const regenerateApiKey = async () => {
  return await api.post('/api/settings/api-key/regenerate');
};

export const updateProfile = async (data) => {
  return await api.put('/api/settings/profile', data);
};