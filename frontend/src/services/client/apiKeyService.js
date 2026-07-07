import api from './api';

const apiKeyService = {
  async getKeys() {
    return await api.get('/api/client/keys');
  },

  async createKey(name) {
    return await api.post('/api/client/keys', { name });
  },

  async updateKeyStatus(keyId, isActive) {
    return await api.put(`/api/client/keys/${keyId}/status`, { is_active: isActive });
  },

  async deleteKey(keyId) {
    return await api.delete(`/api/client/keys/${keyId}`);
  },
};

export default apiKeyService;
