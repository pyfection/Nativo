import axios from 'axios';
import { enqueue, isNetworkError, QueuedOffline } from './outbox';
import { clearReads, loadRead, saveRead } from './readCache';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Offline copies of API reads (readCache.ts) can hold the signed-in
 *  user's data, so they are dropped whenever the session ends. */
export function clearApiCache() {
  void clearReads();
}

// Token management is never kept offline.
const keepsOfflineCopy = (url?: string) => !url?.startsWith('/api/v1/auth/tokens');

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
  (response) => {
    const { config } = response;
    if (config.method === 'get' && response.status === 200 && keepsOfflineCopy(config.url)) {
      void saveRead(api.getUri(config), response.data);
    }
    return response;
  },
  async (error) => {
    // No connection: reads fall back to their last copy, and writes that
    // opted in wait in the outbox (see outbox.ts).
    if (isNetworkError(error) && error.config) {
      if (error.config.method === 'get') {
        const saved = await loadRead(api.getUri(error.config));
        if (saved) return { data: saved.data, status: 200, statusText: 'OK', headers: {}, config: error.config };
      } else if (error.config.outbox && (await enqueue(error.config))) {
        return Promise.reject(new QueuedOffline());
      }
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

