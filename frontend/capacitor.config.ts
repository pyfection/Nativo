import type { CapacitorConfig } from '@capacitor/cli';

// Store apps (Android + iOS) wrapping the built web app in dist/. See MOBILE.md.
// The app talks to VITE_API_URL like the website does; the API must allow the
// app origins https://localhost (Android) and capacitor://localhost (iOS) in
// BACKEND_CORS_ORIGINS.
const config: CapacitorConfig = {
  // Permanent once published to a store.
  appId: 'io.github.pyfection.nativo',
  appName: 'Nativo',
  webDir: 'dist',
  plugins: {
    // Edge-to-edge on Android: the page pads itself with env(safe-area-inset-*)
    // (index.html sets viewport-fit=cover).
    SystemBars: { insetsHandling: 'native' },
  },
};

export default config;
