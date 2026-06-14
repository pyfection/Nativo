import { useState, useEffect } from 'react';
import wordService, {
  LexemeWithForms,
  TranslationLink,
} from '../services/wordService';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
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
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchDirection, setSearchDirection] = useState<SearchDirection>('current-to-known');
  const [selectedKnownLanguages, setSelectedKnownLanguages] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<ResultWithTranslations[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const knownLanguages = languages.filter((lang) => {
    if (!user?.language_proficiencies) return false;
    const proficiency = user.language_proficiencies.find((lp) => lp.language_id === lang.id);
    if (!proficiency) return false;
    const level = proficiency.proficiency_level.toLowerCase();
    return level === 'intermediate' || level === 'fluent' || level === 'native';
  });

  useEffect(() => {
    setSelectedKnownLanguages(new Set(knownLanguages.map((lang) => lang.id)));
  }, [user, languages]);

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
      setError(detail ? `${detail}${suffix}` : `Failed to search words${suffix}`);
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
    translations.forEach((t) => {
      const langName = t.language_name || 'Unknown';
      if (!grouped[langName]) grouped[langName] = [];
      grouped[langName].push(t);
    });
    return grouped;
  };

  const findLemmaForm = (lexeme: LexemeWithForms) =>
    lexeme.forms?.find((f) => f.is_lemma) ?? lexeme.forms?.[0];

  return (
    <div className="dictionary-page">
      <div className="dictionary-header">
        <h1>Dictionary</h1>
        <p className="subtitle">Look up words and their translations</p>
      </div>

      <div className="search-section">
        <div className="search-controls">
          <input
            type="text"
            className="search-input"
            placeholder="Enter word to search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className="search-button"
            onClick={handleSearch}
            disabled={loading || !searchQuery.trim()}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="direction-toggle">
          <button className="toggle-button" onClick={toggleSearchDirection}>
            <span className="toggle-label">Search direction:</span>
            <span className="toggle-value">
              {searchDirection === 'current-to-known'
                ? `${selectedLanguage.name} → Known Languages`
                : `Known Languages → ${selectedLanguage.name}`}
            </span>
          </button>
        </div>

        {knownLanguages.length > 0 && (
          <div className="language-filters">
            <span className="filter-label">Filter by known languages:</span>
            <div className="language-toggles">
              {knownLanguages.map((lang) => (
                <button
                  key={lang.id}
                  className={`language-toggle ${selectedKnownLanguages.has(lang.id) ? 'active' : ''}`}
                  onClick={() => toggleKnownLanguage(lang.id)}
                >
                  {lang.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {knownLanguages.length === 0 && (
          <div className="no-known-languages">
            <p>You haven't joined any languages yet.</p>
            <p className="hint">
              Join languages with intermediate or higher proficiency to use the dictionary.
            </p>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {results.length > 0 && (
        <div className="results-section">
          <h2 className="results-title">Results ({results.length})</h2>
          <div className="results-list">
            {results.map((lexeme) => {
              const lemmaForm = findLemmaForm(lexeme);
              return (
                <div key={lexeme.id} className="word-result-card">
                  <div className="word-header">
                    <div className="word-info">
                      <h3 className="word-text">{lexeme.lemma}</h3>
                      {lemmaForm?.romanization && (
                        <span className="word-romanization">({lemmaForm.romanization})</span>
                      )}
                      {lexeme.part_of_speech && (
                        <span className="word-pos">{lexeme.part_of_speech}</span>
                      )}
                    </div>
                  </div>

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
                      No translations available in selected languages
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
          <p>No results found for "{searchQuery}"</p>
        </div>
      )}
    </div>
  );
}
