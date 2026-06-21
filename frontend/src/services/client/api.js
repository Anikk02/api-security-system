import axios from 'axios';
import { API_BASE_URL } from '../../utils/client/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token here if needed in future
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,

  (error) => {
    // 🔴 Server responded (real API error)
    if (error.response) {
      console.error("API Error:", error.response.data);
    }

    // ⚠️ No response → backend down / network issue
    else if (error.request) {
      console.warn("⚠️ Backend not reachable (using fallback)");
    }

    // ❗ Unexpected error
    else {
      console.error("Unexpected Error:", error.message);
    }

    return Promise.reject(error);
  }
);

export default api;