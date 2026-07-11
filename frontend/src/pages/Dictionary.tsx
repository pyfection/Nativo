import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import wordService, {
  LexemeWithForms,
  TranslationLink,
} from '../services/wordService';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { languageDisplayName } from '../utils/languageName';
import './Dictionary.css';

interface DictionaryProps {
  selectedLanguage: Language;
  languages: Language[];
}

type SearchDirection = 'current-to-known' | 'known-to-current';

interface ResultWithTranslations extends LexemeWithForms {
  translations: TranslationLink[];
}

export default function Dictionary({ selectedLanguage, languages }: DictionaryProps) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchDirection, setSearchDirection] = useState<SearchDirection>('current-to-known');
  const [selectedKnownLanguages, setSelectedKnownLanguages] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<ResultWithTranslations[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const proficiencyLanguages = languages.filter((lang) => {
    if (!user?.language_proficiencies) return false;
    const proficiency = user.language_proficiencies.find((lp) => lp.language_id === lang.id);
    if (!proficiency) return false;
    const level = proficiency.proficiency_level.toLowerCase();
    return level === 'intermediate' || level === 'fluent' || level === 'native';
  });

  // Guests (and members who haven't joined a language yet) can still use the
  // dictionary: fall back to every other language as a candidate target.
  const usingProficiencies = proficiencyLanguages.length > 0;
  const knownLanguages = usingProficiencies
    ? proficiencyLanguages
    : languages.filter((lang) => lang.id !== selectedLanguage.id);

  useEffect(() => {
    setSelectedKnownLanguages(new Set(knownLanguages.map((lang) => lang.id)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, languages, selectedLanguage.id]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError('');

      const language_ids =
        searchDirection === 'current-to-known'
          ? selectedLanguage.id
          : Array.from(selectedKnownLanguages).join(',');

      const data = await wordService.search({ q: searchQuery, language_ids });

      // Translations are now a separate endpoint; fetch in parallel and merge.
      const withTranslations = await Promise.all(
        data.map(async (lexeme) => {
          const translations = await wordService.listTranslations(lexeme.id);
          const filtered =
            searchDirection === 'current-to-known'
              ? translations.filter((t) => selectedKnownLanguages.has(t.language_id))
              : translations.filter((t) => t.language_id === selectedLanguage.id);
          return { ...lexeme, translations: filtered };
        }),
      );

      setResults(withTranslations);
    } catch (err: any) {
      console.error('Search error:', err);
      // Surface the HTTP status when we have one so users can at least tell
      // network errors apart from server 500s when reporting issues.
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const suffix = status ? ` (HTTP ${status})` : '';
      setError(detail ? `${detail}${suffix}` : `${t('dictionary_page.search_failed')}${suffix}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleKnownLanguage = (languageId: string) => {
    const next = new Set(selectedKnownLanguages);
    if (next.has(languageId)) next.delete(languageId);
    else next.add(languageId);
    setSelectedKnownLanguages(next);
  };

  const toggleSearchDirection = () => {
    setSearchDirection((prev) =>
      prev === 'current-to-known' ? 'known-to-current' : 'current-to-known',
    );
    setResults([]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const groupTranslationsByLanguage = (translations: TranslationLink[]) => {
    const grouped: { [key: string]: TranslationLink[] } = {};
    translations.forEach((tr) => {
      const lang = languages.find((l) => l.id === tr.language_id);
      const langName = lang
        ? languageDisplayName(lang)
        : tr.language_name || t('dictionary_page.unknown_language');
      if (!grouped[langName]) grouped[langName] = [];
      grouped[langName].push(tr);
    });
    return grouped;
  };

  const findLemmaForm = (lexeme: LexemeWithForms) =>
    lexeme.forms?.find((f) => f.is_lemma) ?? lexeme.forms?.[0];

  return (
    <div className="dictionary-page">
      <div className="dictionary-header">
        <h1>{t('dictionary_page.title')}</h1>
        <p className="subtitle">{t('dictionary_page.subtitle')}</p>
      </div>

      <div className="search-section">
        <div className="search-controls">
          <input
            type="text"
            className="search-input"
            placeholder={t('dictionary_page.search_placeholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className="search-button"
            onClick={handleSearch}
            disabled={loading || !searchQuery.trim()}
          >
            {loading ? t('dictionary_page.searching') : t('dictionary_page.search')}
          </button>
        </div>

        <div className="direction-toggle">
          <button className="toggle-button" onClick={toggleSearchDirection}>
            <span className="toggle-label">{t('dictionary_page.search_direction')}</span>
            <span className="toggle-value">
              {searchDirection === 'current-to-known'
                ? `${languageDisplayName(selectedLanguage)} → ${usingProficiencies ? t('dictionary_page.known_languages') : t('dictionary_page.other_languages')}`
                : `${usingProficiencies ? t('dictionary_page.known_languages') : t('dictionary_page.other_languages')} → ${languageDisplayName(selectedLanguage)}`}
            </span>
          </button>
        </div>

        {knownLanguages.length > 0 && (
          <div className="language-filters">
            <span className="filter-label">
              {usingProficiencies
                ? t('dictionary_page.filter_by_known_languages')
                : t('dictionary_page.filter_by_language')}
            </span>
            <div className="language-toggles">
              {knownLanguages.map((lang) => (
                <button
                  key={lang.id}
                  className={`language-toggle ${selectedKnownLanguages.has(lang.id) ? 'active' : ''}`}
                  onClick={() => toggleKnownLanguage(lang.id)}
                >
                  {languageDisplayName(lang)}
                </button>
              ))}
            </div>
          </div>
        )}

        {knownLanguages.length === 0 && (
          <div className="no-known-languages">
            <p>{t('dictionary_page.no_other_language')}</p>
            <p className="hint">
              {t('dictionary_page.no_other_language_hint', {
                language: languageDisplayName(selectedLanguage),
              })}
            </p>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {results.length > 0 && (
        <div className="results-section">
          <h2 className="results-title">{t('dictionary_page.results_title', { count: results.length })}</h2>
          <div className="results-list">
            {results.map((lexeme) => {
              const lemmaForm = findLemmaForm(lexeme);
              const otherForms = (lexeme.forms ?? []).filter((f) => !f.is_lemma);
              return (
                <div key={lexeme.id} className="word-result-card">
                  <div className="word-header">
                    <div className="word-info">
                      <Link to={`/words/${lexeme.id}`} className="word-text-link">
                        <h3 className="word-text">{lexeme.lemma}</h3>
                      </Link>
                      {lemmaForm?.romanization && (
                        <span className="word-romanization">({lemmaForm.romanization})</span>
                      )}
                      {lemmaForm?.ipa_pronunciation && (
                        <span className="word-ipa">[{lemmaForm.ipa_pronunciation}]</span>
                      )}
                      {lexeme.part_of_speech && (
                        <span className="word-pos">{lexeme.part_of_speech}</span>
                      )}
                    </div>
                  </div>
                  {otherForms.length > 0 && (
                    <div className="word-forms-row">
                      <span className="word-forms-label">{t('dictionary_page.forms_label')}</span>
                      {otherForms.map((f) => (
                        <span key={f.id} className="word-form-chip" title={f.notes ?? undefined}>
                          {f.form}
                          {f.notes && <em className="word-form-chip-note"> · {f.notes}</em>}
                        </span>
                      ))}
                    </div>
                  )}

                  {lexeme.translations.length > 0 ? (
                    <div className="translations-section">
                      {Object.entries(groupTranslationsByLanguage(lexeme.translations)).map(
                        ([langName, translations]) => (
                          <div key={langName} className="language-group">
                            <h4 className="language-name">{langName}</h4>
                            <div className="translations-list">
                              {translations.map((trans) => (
                                <div key={trans.id} className="translation-item">
                                  <div className="translation-word">
                                    <span className="trans-text">{trans.lemma}</span>
                                    {trans.part_of_speech && (
                                      <span className="trans-pos">{trans.part_of_speech}</span>
                                    )}
                                  </div>
                                  {trans.notes && (
                                    <div className="translation-notes">
                                      <span>{trans.notes}</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    <div className="no-translations">
                      {t('dictionary_page.no_translations')}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && searchQuery && results.length === 0 && !error && (
        <div className="no-results">
          <p>{t('dictionary_page.no_results', { query: searchQuery })}</p>
        </div>
      )}
    </div>
  );
}
