/**
 * Per-language dark theme derivation.
 *
 * The new design has 5 colour slots that move together: an accent (CTAs and
 * highlights), a deep variant of the accent (used as foreground on accent
 * buttons), two dark background tones (used in the radial gradient), and a
 * glow tone for the top-right radial.
 *
 * Most languages only have a single primary colour stored in the DB. We
 * compute the rest by HSL-shifting from that primary. The few language ISOs
 * we have hand-tuned palettes for (Bavarian and the design-doc demo set)
 * override the derived values.
 *
 * The CSS variables this returns are merged onto the root wrapper of the app
 * so global styles can reference them: `--accent`, `--accent-deep`,
 * `--base1`, `--base2`, `--glow`. For backwards compatibility with pages
 * still using the old tokens we ALSO emit `--primary`, `--secondary`,
 * `--accent-legacy`, `--background`.
 */

export interface ThemePalette {
  accent: string;
  accentDeep: string;
  base1: string;
  base2: string;
  glow: string;
}

export interface LanguageColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

// Hand-tuned palettes pulled from the nativo-hero-v2 design doc and
// any future curator overrides. Keyed by ISO 639-3.
const OVERRIDES: Record<string, ThemePalette> = {
  bar: {
    accent: '#5DA9E9',
    accentDeep: '#06243f',
    base1: '#0a2733',
    base2: '#061d2a',
    glow: '#155f9c',
  },
  cym: {
    accent: '#EC6A5E',
    accentDeep: '#3a100b',
    base1: '#241315',
    base2: '#170d10',
    glow: '#9c3b33',
  },
  mri: {
    accent: '#36C2A6',
    accentDeep: '#04241e',
    base1: '#0a2a27',
    base2: '#061d1b',
    glow: '#0f8a72',
  },
  gle: {
    accent: '#54B776',
    accentDeep: '#0c2614',
    base1: '#112a1c',
    base2: '#0a1d13',
    glow: '#2f8a4f',
  },
};

/**
 * Compute the dark palette from a single accent hex by shifting its HSL.
 *
 * - accent: the input, unchanged. Use a vivid mid-light colour (~60% L).
 * - accentDeep: same hue, slightly desaturated, very dark (~14% L).
 * - base1: same hue, low chroma, dark (~10% L).
 * - base2: same hue, slightly more chroma, darker (~7% L).
 * - glow: same hue, medium chroma, mid-dark (~33% L).
 */
export function deriveTheme(accentHex: string): ThemePalette {
  const [h, s] = hexToHsl(accentHex);
  return {
    accent: accentHex,
    accentDeep: hslToHex(h, Math.min(s, 80), 14),
    base1: hslToHex(h, Math.min(s, 35), 10),
    base2: hslToHex(h, Math.min(s, 40), 7),
    glow: hslToHex(h, Math.min(s, 65), 33),
  };
}

export function getThemeForLanguage(language: {
  iso: string;
  colorScheme: LanguageColorScheme;
}): ThemePalette {
  return OVERRIDES[language.iso] ?? deriveTheme(language.colorScheme.primary);
}

/**
 * Returns a `style` object suitable for spreading onto a wrapper element
 * (e.g. `style={getThemeStyles(language)}`). Sets both the new tokens and
 * the legacy `--primary` family so unmigrated CSS keeps working.
 */
export function getThemeStyles(language: {
  iso: string;
  colorScheme: LanguageColorScheme;
}): React.CSSProperties {
  const t = getThemeForLanguage(language);
  // The legacy tokens are derived from the new palette to stay consistent
  // while we migrate per-page CSS over.
  return {
    '--accent': t.accent,
    '--accent-deep': t.accentDeep,
    '--base1': t.base1,
    '--base2': t.base2,
    '--glow': t.glow,
    // Back-compat
    '--primary': t.accent,
    '--secondary': t.accentDeep,
    '--accent-legacy': language.colorScheme.accent,
    '--background': t.base1,
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
