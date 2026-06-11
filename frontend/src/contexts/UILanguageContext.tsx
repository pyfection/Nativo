import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react';
import i18n from '../i18n';

import { Language } from '../App';

const UI_LANGUAGE_KEY = 'nativo_ui_language_id';

interface UILanguageContextValue {
  uiLanguage: Language | null;
  setUILanguageId: (id: string) => void;
  /** All languages available to pick as UI language. */
  candidates: Language[];
}

const UILanguageContext = createContext<UILanguageContextValue | null>(null);

function pickDefault(languages: Language[]): Language | null {
  if (languages.length === 0) return null;
  return (
    languages.find((l) => l.name.toLowerCase() === 'english') ??
    languages[0]
  );
}

interface UILanguageProviderProps {
  languages: Language[];
  children: ReactNode;
}

export function UILanguageProvider({ languages, children }: UILanguageProviderProps) {
  const [uiLanguageId, setUILanguageIdState] = useState<string | null>(() => {
    const saved = localStorage.getItem(UI_LANGUAGE_KEY);
    if (saved && languages.some((l) => l.id === saved)) return saved;
    return pickDefault(languages)?.id ?? null;
  });

  // If languages list changes (initial load) and we haven't picked one, pick now.
  useEffect(() => {
    if (uiLanguageId && languages.some((l) => l.id === uiLanguageId)) return;
    const id = pickDefault(languages)?.id ?? null;
    if (id) setUILanguageIdState(id);
  }, [languages, uiLanguageId]);

  useEffect(() => {
    if (uiLanguageId) localStorage.setItem(UI_LANGUAGE_KEY, uiLanguageId);
  }, [uiLanguageId]);

  // Keep i18next in sync with the picker. Bundles that don't exist fall back
  // to English via the i18n config.
  useEffect(() => {
    const lang = languages.find((l) => l.id === uiLanguageId);
    if (lang?.iso) void i18n.changeLanguage(lang.iso);
  }, [languages, uiLanguageId]);

  const value = useMemo<UILanguageContextValue>(
    () => ({
      uiLanguage: languages.find((l) => l.id === uiLanguageId) ?? null,
      setUILanguageId: setUILanguageIdState,
      candidates: languages,
    }),
    [languages, uiLanguageId]
  );

  return <UILanguageContext.Provider value={value}>{children}</UILanguageContext.Provider>;
}

export function useUILanguage(): UILanguageContextValue {
  const ctx = useContext(UILanguageContext);
  if (!ctx) {
    throw new Error('useUILanguage must be used within a UILanguageProvider');
  }
  return ctx;
}
