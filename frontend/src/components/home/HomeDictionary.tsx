import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../../App';
import { useUILanguage } from '../../contexts/UILanguageContext';
import wordService, { WordWithTranslations } from '../../services/wordService';
import './HomeDictionary.css';

interface HomeDictionaryProps {
  selectedLanguage: Language;
}

export default function HomeDictionary({ selectedLanguage }: HomeDictionaryProps) {
  const { t } = useTranslation();
  const { uiLanguage } = useUILanguage();
  // If the page UI language happens to be the same as the source, fall back
  // to "no target" — the widget will then list any translations it gets back.
  const targetLanguage =
    uiLanguage && uiLanguage.id !== selectedLanguage.id ? uiLanguage : null;

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<WordWithTranslations[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setSubmitted(true);
    try {
      const data = await wordService.search({
        q: trimmed,
        language_ids: selectedLanguage.id,
        include_translations: true,
      });
      setResults(data);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setError(t('dictionary.rate_limited'));
      } else {
        setError(err.response?.data?.detail || t('dictionary.search_failed'));
      }
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const ctx = { source: selectedLanguage.name, target: targetLanguage?.name ?? '' };

  return (
    <section className="home-dictionary">
      <div className="home-dictionary-inner">
        <h3 className="home-dictionary-title">
          {targetLanguage
            ? t('dictionary.title_with_target', ctx)
            : t('dictionary.title_no_target', ctx)}
        </h3>
        <p className="home-dictionary-subtitle">
          {targetLanguage
            ? t('dictionary.subtitle_with_target', ctx)
            : t('dictionary.subtitle_no_target', ctx)}
        </p>

        <div className="home-dictionary-form">
          <input
            type="text"
            className="home-dictionary-input"
            placeholder={t('dictionary.placeholder', ctx)}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
            aria-label={t('dictionary.search_aria_label', ctx)}
          />
          <button
            type="button"
            className="home-dictionary-button"
            onClick={handleSearch}
            disabled={loading || !query.trim()}
          >
            {loading ? t('dictionary.searching') : t('dictionary.search')}
          </button>
        </div>

        {error && <p className="home-dictionary-error">{error}</p>}

        {submitted && !loading && !error && results.length === 0 && (
          <p className="home-dictionary-empty">{t('dictionary.empty', { query })}</p>
        )}

        {results.length > 0 && (
          <ul className="home-dictionary-results">
            {results.map((word) => {
              const targetTranslations = targetLanguage
                ? word.translations.filter((tr) => tr.language_id === targetLanguage.id)
                : [];
              return (
                <li key={word.id} className="home-dictionary-result">
                  <div className="home-dictionary-headword">
                    <span className="home-dictionary-word">{word.word}</span>
                    {word.romanization && (
                      <span className="home-dictionary-roman">/{word.romanization}/</span>
                    )}
                    {word.part_of_speech && (
                      <span className="home-dictionary-pos">{word.part_of_speech}</span>
                    )}
                  </div>
                  {targetTranslations.length === 0 ? (
                    <p className="home-dictionary-no-trans">
                      {targetLanguage
                        ? t('dictionary.no_target_translation', ctx)
                        : t('dictionary.no_translations')}
                    </p>
                  ) : (
                    <p className="home-dictionary-trans-words">
                      {targetTranslations.map((tr) => tr.word).join(', ')}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
