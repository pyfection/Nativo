import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [
    react(),
    // Installable app that works offline. The manifest is public/site.webmanifest.
    // The service worker precaches the built app, and keeps a copy of API reads
    // (network first, so data is live whenever there's a connection) for
    // offline use. Writes made offline are queued by src/services/outbox.ts.
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false,
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'],
      workbox: {
        navigateFallbackDenylist: [/^\/(api|admin|mcp|uploads)(\/|$)/],
        runtimeCaching: [
          {
            // API reads, on whatever origin VITE_API_URL points at. Cleared
            // on logout (clearApiCache in api.ts). Token management stays live-only.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' &&
              url.pathname.startsWith('/api/v1/') &&
              !url.pathname.startsWith('/api/v1/auth/tokens'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'nativo-api',
              networkTimeoutSeconds: 6,
              expiration: { maxEntries: 1000, maxAgeSeconds: 30 * 24 * 60 * 60 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            urlPattern: ({ url }) =>
              url.origin === 'https://fonts.googleapis.com' ||
              url.origin === 'https://fonts.gstatic.com',
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'google-fonts' },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: Number(process.env.PORT) || 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
