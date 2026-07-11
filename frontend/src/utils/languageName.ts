import i18n from '../i18n';

interface HasLanguageName {
  name: string;
  /** Frontend Language type carries `iso`; API responses carry `iso_639_3`. */
  iso?: string;
  iso_639_3?: string | null;
}

/**
 * Language names shown in the UI, localized to the interface language.
 *
 * Language rows in the database store one (English) `name`; the locale files
 * carry a `language_names.<iso>` map so "Bavarian" can render as "Bávaro" in
 * a Spanish interface. Unknown languages fall back to the stored name.
 */
export function languageDisplayName(lang: HasLanguageName): string {
  const iso = lang.iso || lang.iso_639_3;
  if (iso && i18n.exists(`language_names.${iso}`)) {
    return i18n.t(`language_names.${iso}`);
  }
  return lang.name;
}

interface HasLanguageDescription extends HasLanguageName {
  description?: string | null;
}

/** Same idea for the (seeded) language descriptions. */
export function languageDisplayDescription(lang: HasLanguageDescription): string {
  const iso = lang.iso || lang.iso_639_3;
  if (iso && i18n.exists(`language_descriptions.${iso}`)) {
    return i18n.t(`language_descriptions.${iso}`);
  }
  return lang.description || '';
}
