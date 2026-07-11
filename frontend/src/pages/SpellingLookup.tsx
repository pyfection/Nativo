import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import wordService, { SpellingResolution } from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
import './SpellingLookup.css';

interface SpellingLookupProps {
  selectedLanguage: Language;
}

/**
 * "How do I write this properly?" — resolves a word the user typed in a
 * non-standard way to its standard spelling for the current language.
 *
 * Backed by GET /api/v1/words/spellings/resolve. Three outcomes: the token is
 * already standard, it maps to one or more standard forms (a known variant), or
 * it's unknown to the dictionary.
 */
export default function SpellingLookup({ selectedLanguage }: SpellingLookupProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<SpellingResolution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLookup = async () => {
    const token = query.trim();
    if (!token) {
      setResult(null);
      return;
    }
    try {
      setLoading(true);
      setError('');
      const data = await wordService.resolveSpelling(selectedLanguage.id, token);
      setResult(data);
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const suffix = status ? ` (HTTP ${status})` : '';
      setError(detail ? `${detail}${suffix}` : t('spelling_page.error_lookup', { suffix }));
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleLookup();
  };

  return (
    <div className="spelling-lookup-page">
      <div className="spelling-lookup-header">
        <h1>{t('spelling_page.title')}</h1>
        <p className="subtitle">
          {t('spelling_page.subtitle', { language: languageDisplayName(selectedLanguage) })}
        </p>
      </div>

      <div className="spelling-lookup-search">
        <input
          type="text"
          className="spelling-lookup-input"
          placeholder={t('spelling_page.input_placeholder', {
            language: languageDisplayName(selectedLanguage),
          })}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          autoFocus
        />
        <button
          type="button"
          className="spelling-lookup-button"
          onClick={handleLookup}
          disabled={loading || !query.trim()}
        >
          {loading ? t('spelling_page.looking_up') : t('spelling_page.look_up')}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && !error && (
        <div className="spelling-lookup-result">
          {result.already_standard ? (
            <div className="spelling-lookup-standard">
              <span className="spelling-lookup-ok">✓</span>
              <span>
                <strong>“{result.token}”</strong> {t('spelling_page.already_standard_post')}
              </span>
            </div>
          ) : result.candidates.length > 0 ? (
            <>
              <p className="spelling-lookup-lead">
                <strong>“{result.token}”</strong> {t('spelling_page.usually_written_post')}
              </p>
              <ul className="spelling-lookup-candidates">
                {result.candidates.map((c) => (
                  <li key={c.word_form_id} className="spelling-lookup-candidate">
                    <span className="spelling-lookup-arrow">→</span>
                    <Link to={`/words/${c.lexeme_id}`} className="spelling-lookup-form">
                      {c.standard_form}
                    </Link>
                    {c.lemma !== c.standard_form && (
                      <span className="spelling-lookup-lemma">({c.lemma})</span>
                    )}
                    {c.note && <span className="spelling-lookup-note">· {c.note}</span>}
                  </li>
                ))}
              </ul>
              {result.candidates.length > 1 && (
                <p className="spelling-lookup-ambiguous">
                  {t('spelling_page.ambiguous')}
                </p>
              )}
            </>
          ) : (
            <div className="spelling-lookup-none">
              {t('spelling_page.not_found_pre')} <strong>“{result.token}”</strong>
              {t('spelling_page.not_found_post')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
