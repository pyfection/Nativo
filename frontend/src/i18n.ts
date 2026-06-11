import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from './locales/en/common.json';
import barCommon from './locales/bar/common.json';

// Keep bundles small and bundled with the JS for sub-ms lookups on first
// paint. When a real i18n workflow lands (Crowdin / Weblate), these JSON
// files become the source of truth that translators edit.
const resources = {
  en: { common: enCommon },
  bar: { common: barCommon },
} as const;

void i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  ns: ['common'],
  defaultNS: 'common',
  interpolation: { escapeValue: false },
  returnEmptyString: false,
});

export default i18n;
