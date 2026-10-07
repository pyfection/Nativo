import axios from 'axios';
import { enqueue, isNetworkError, QueuedOffline } from './outbox';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Service-worker cache of API reads (see vite.config.ts). It can hold the
 *  signed-in user's data, so it is dropped whenever the session ends. */
export function clearApiCache() {
  if ('caches' in window) void caches.delete('nativo-api');
}

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
  async (error) => {
    // No connection: writes that opted in wait in the outbox (see outbox.ts).
    if (isNetworkError(error) && error.config?.outbox && error.config.method !== 'get') {
      if (await enqueue(error.config)) return Promise.reject(new QueuedOffline());
    }
    const hadToken = !!localStorage.getItem('access_token');
    if (error.response?.status === 401 && hadToken) {
      localStorage.removeItem('access_token');
      clearApiCache();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

