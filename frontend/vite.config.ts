import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [
    react(),
    // Installable web app. The manifest is public/site.webmanifest. The
    // service worker only precaches the built app so it opens offline; API
    // data offline is handled in the app (services/readCache.ts, outbox.ts)
    // so it also works in the store apps, which don't use the worker.
    // Registered from src/index.tsx (web only).
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false,
      manifest: false,
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'icon-192.png', 'icon-512.png'],
      workbox: {
        navigateFallbackDenylist: [/^\/(api|admin|mcp|uploads)(\/|$)/],
        runtimeCaching: [
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
