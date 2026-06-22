import api from './api';

const authService = {
  async register(email, password, companyName) {
    return await api.post('/api/auth/register', {
      email,
      password,
      company_name: companyName || null,
    });
  },

  async login(email, password) {
    const data = await api.post('/api/auth/login', {
      email,
      password,
    });
    if (data && data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    return data;
  },

  async getMe() {
    return await api.get('/api/auth/me');
  },

  async logout(refreshToken) {
    try {
      await api.post('/api/auth/logout', { refresh_token: refreshToken });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
};

export default authService;
