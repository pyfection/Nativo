import { useState } from 'react';

import { Language } from '../../App';
import { useUILanguage } from '../../contexts/UILanguageContext';
import wordService, { WordWithTranslations } from '../../services/wordService';
import './HomeDictionary.css';

interface HomeDictionaryProps {
  selectedLanguage: Language;
}

export default function HomeDictionary({ selectedLanguage }: HomeDictionaryProps) {
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
        setError('Too many requests — please slow down and try again in a minute.');
      } else {
        setError(err.response?.data?.detail || 'Search failed. Please try again.');
      }
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="home-dictionary">
      <div className="home-dictionary-inner">
        <h3 className="home-dictionary-title">
          {targetLanguage
            ? `Look up a ${selectedLanguage.name} word → ${targetLanguage.name}`
            : `Look up a word in ${selectedLanguage.name}`}
        </h3>
        <p className="home-dictionary-subtitle">
          {targetLanguage
            ? `Search ${selectedLanguage.name} vocabulary and see ${targetLanguage.name} translations. Change the target via the language picker in the header.`
            : `Search ${selectedLanguage.name} vocabulary.`}
        </p>

        <div className="home-dictionary-form">
          <input
            type="text"
            className="home-dictionary-input"
            placeholder={`Type a ${selectedLanguage.name} word…`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
            aria-label={`Search ${selectedLanguage.name} words`}
          />
          <button
            type="button"
            className="home-dictionary-button"
            onClick={handleSearch}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {error && <p className="home-dictionary-error">{error}</p>}

        {submitted && !loading && !error && results.length === 0 && (
          <p className="home-dictionary-empty">
            No matches for &ldquo;{query}&rdquo; yet. Contributors are still building this dictionary.
          </p>
        )}

        {results.length > 0 && (
          <ul className="home-dictionary-results">
            {results.map((word) => {
              const targetTranslations = targetLanguage
                ? word.translations.filter((t) => t.language_id === targetLanguage.id)
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
                        ? `No ${targetLanguage.name} translation yet.`
                        : 'No translations yet.'}
                    </p>
                  ) : (
                    <p className="home-dictionary-trans-words">
                      {targetTranslations.map((t) => t.word).join(', ')}
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
