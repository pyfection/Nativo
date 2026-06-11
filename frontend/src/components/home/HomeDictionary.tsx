import { useState } from 'react';

import { Language } from '../../App';
import wordService, { WordWithTranslations } from '../../services/wordService';
import './HomeDictionary.css';

interface HomeDictionaryProps {
  selectedLanguage: Language;
}

interface GroupedTranslations {
  [languageName: string]: WordWithTranslations['translations'];
}

function groupByLanguage(translations: WordWithTranslations['translations']): GroupedTranslations {
  return translations.reduce<GroupedTranslations>((acc, t) => {
    const key = t.language_name || 'Unknown';
    (acc[key] ||= []).push(t);
    return acc;
  }, {});
}

export default function HomeDictionary({ selectedLanguage }: HomeDictionaryProps) {
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
          Look up a word in {selectedLanguage.name}
        </h3>
        <p className="home-dictionary-subtitle">
          Search across {selectedLanguage.name} vocabulary and see translations in other languages.
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
              const groups = groupByLanguage(word.translations);
              const languageNames = Object.keys(groups);
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
                  {languageNames.length === 0 ? (
                    <p className="home-dictionary-no-trans">No translations yet.</p>
                  ) : (
                    languageNames.map((lang) => (
                      <div key={lang} className="home-dictionary-trans-group">
                        <span className="home-dictionary-trans-lang">{lang}</span>
                        <span className="home-dictionary-trans-words">
                          {groups[lang].map((t) => t.word).join(', ')}
                        </span>
                      </div>
                    ))
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
