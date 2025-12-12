import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle error responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - redirect to login (except for password reset endpoints)
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      // Don't redirect on password reset endpoints
      if (!url.includes('/password-reset')) {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    
    // Log network errors for debugging
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('Network error:', {
        url: error.config?.url,
        method: error.config?.method,
        message: error.message
      });
    }
    
    // Log timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      console.error('Request timeout:', {
        url: error.config?.url,
        method: error.config?.method,
        timeout: error.config?.timeout
      });
    }
    
    return Promise.reject(error);
  }
);

export default api;

