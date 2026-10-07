/**
 * Per-language accent derivation.
 *
 * Backgrounds and text are language-agnostic (graphite dark / paper light,
 * see src/index.css). Only the accent follows the selected language: two
 * slots, an accent (CTAs and highlights) and a deep variant of it (used as
 * foreground on accent buttons in the dark theme).
 *
 * Most languages only have a single primary colour stored in the DB. We
 * compute the deep variant by HSL-shifting from that primary. The few
 * language ISOs we have hand-tuned palettes for override the derived values.
 *
 * The CSS variables this returns are set on <html>: `--lang-accent` and
 * `--lang-accent-deep`. index.css maps them onto `--accent` /
 * `--accent-deep` per theme (the light theme darkens the accent so accent
 * text stays readable on paper).
 */

export interface ThemePalette {
  accent: string;
  accentDeep: string;
}

export interface LanguageColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

// Hand-tuned palettes keyed by ISO 639-3.
const OVERRIDES: Record<string, ThemePalette> = {
  bar: { accent: '#5DA9E9', accentDeep: '#06243f' },
  cym: { accent: '#EC6A5E', accentDeep: '#3a100b' },
  mri: { accent: '#36C2A6', accentDeep: '#04241e' },
  gle: { accent: '#54B776', accentDeep: '#0c2614' },
};

/**
 * Compute the palette from a single accent hex by shifting its HSL.
 *
 * - accent: the input, unchanged. Use a vivid mid-light colour (~60% L).
 * - accentDeep: same hue, slightly desaturated, very dark (~14% L).
 */
export function deriveTheme(accentHex: string): ThemePalette {
  const [h, s] = hexToHsl(accentHex);
  return {
    accent: accentHex,
    accentDeep: hslToHex(h, Math.min(s, 80), 14),
  };
}

export function getThemeForLanguage(language: {
  iso: string;
  colorScheme: LanguageColorScheme;
}): ThemePalette {
  return OVERRIDES[language.iso] ?? deriveTheme(language.colorScheme.primary);
}

/**
 * Returns the CSS custom properties to set on <html> for a language.
 */
export function getThemeStyles(language: {
  iso: string;
  colorScheme: LanguageColorScheme;
}): React.CSSProperties {
  const t = getThemeForLanguage(language);
  return {
    '--lang-accent': t.accent,
    '--lang-accent-deep': t.accentDeep,
  } as React.CSSProperties;
}

// ---------------------------------------------------------------------------
// Colour math helpers
// ---------------------------------------------------------------------------

function hexToHsl(hex: string): [number, number, number] {
  const clean = hex.replace('#', '').padStart(6, '0');
  const r = parseInt(clean.slice(0, 2), 16) / 255;
  const g = parseInt(clean.slice(2, 4), 16) / 255;
  const b = parseInt(clean.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }
  return [h * 360, s * 100, l * 100];
}

function hslToHex(h: number, s: number, l: number): string {
  const hh = ((h % 360) + 360) % 360 / 360;
  const ss = Math.max(0, Math.min(100, s)) / 100;
  const ll = Math.max(0, Math.min(100, l)) / 100;
  let r: number;
  let g: number;
  let b: number;
  if (ss === 0) {
    r = g = b = ll;
  } else {
    const q = ll < 0.5 ? ll * (1 + ss) : ll + ss - ll * ss;
    const p = 2 * ll - q;
    r = hueToRgb(p, q, hh + 1 / 3);
    g = hueToRgb(p, q, hh);
    b = hueToRgb(p, q, hh - 1 / 3);
  }
  const toHex = (v: number) =>
    Math.round(v * 255)
      .toString(16)
      .padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function hueToRgb(p: number, q: number, t: number): number {
  let tt = t;
  if (tt < 0) tt += 1;
  if (tt > 1) tt -= 1;
  if (tt < 1 / 6) return p + (q - p) * 6 * tt;
  if (tt < 1 / 2) return q;
  if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6;
  return p;
}
