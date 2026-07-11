import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from './locales/en/common.json';
import barCommon from './locales/bar/common.json';
import esCommon from './locales/es/common.json';

// Keep bundles small and bundled with the JS for sub-ms lookups on first
// paint. When a real i18n workflow lands (Crowdin / Weblate), these JSON
// files become the source of truth that translators edit.
// The UI language switcher passes ISO 639-3 codes from the Language table
// (bar, spa, eng, …), so bundles are registered under both the common
// two-letter code and the 639-3 code where they differ.
const resources = {
  en: { common: enCommon },
  bar: { common: barCommon },
  es: { common: esCommon },
  spa: { common: esCommon },
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
