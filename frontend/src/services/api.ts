import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

// Handle 401 responses. Only force a redirect when a token was actually
// sent — that means an expired/invalid session. Anonymous visitors browsing
// public pages must never be ejected to /login by a stray 401 from an
// auth-only endpoint; the calling page handles the error itself.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const hadToken = !!localStorage.getItem('access_token');
    if (error.response?.status === 401 && hadToken) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

