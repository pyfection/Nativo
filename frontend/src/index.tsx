import React from 'react';
import ReactDOM from 'react-dom/client';
import { Capacitor } from '@capacitor/core';
import { registerSW } from 'virtual:pwa-register';
import App from './App';
import './i18n';
import './index.css';

// The store apps ship the built files inside the app, so they need no
// service worker (and iOS can't run one under capacitor://).
if (!Capacitor.isNativePlatform()) registerSW({ immediate: true });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
