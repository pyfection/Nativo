import { useCallback, useEffect, useState } from 'react';

/**
 * Light ("paper") / dark ("graphite") colour theme.
 *
 * The theme is just `data-theme` on <html>; index.css switches every token on
 * it. An inline script in index.html sets it before first paint (saved
 * choice, else the OS preference) so there's no flash of the wrong theme.
 * This hook reads it back and lets the header toggle change it.
 */
export type ColorTheme = 'light' | 'dark';

export const THEME_KEY = 'nativo_theme';

const THEME_COLORS: Record<ColorTheme, string> = { dark: '#15171a', light: '#F6F4EF' };

function currentTheme(): ColorTheme {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
}

function applyTheme(theme: ColorTheme) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', THEME_COLORS[theme]);
}

export function useColorTheme() {
  const [theme, setThemeState] = useState<ColorTheme>(currentTheme);

  // Follow OS changes until the user picks a theme explicitly.
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: light)');
    const onChange = (e: MediaQueryListEvent) => {
      if (localStorage.getItem(THEME_KEY)) return;
      const next = e.matches ? 'light' : 'dark';
      applyTheme(next);
      setThemeState(next);
    };
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);

  const setTheme = useCallback((next: ColorTheme) => {
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(currentTheme() === 'light' ? 'dark' : 'light');
  }, [setTheme]);

  return { theme, setTheme, toggleTheme };
}
