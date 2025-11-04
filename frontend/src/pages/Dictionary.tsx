import { useState, useEffect } from 'react';
import wordService, { WordWithTranslations } from '../services/wordService';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import './Dictionary.css';

interface DictionaryProps {
  selectedLanguage: Language;
  languages: Language[];
}

type SearchDirection = 'current-to-known' | 'known-to-current';

export default function Dictionary({ selectedLanguage, languages }: DictionaryProps) {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchDirection, setSearchDirection] = useState<SearchDirection>('current-to-known');
  const [selectedKnownLanguages, setSelectedKnownLanguages] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<WordWithTranslations[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Get user's known languages (intermediate, fluent, native only)
  const knownLanguages = languages.filter(lang => {
    if (!user?.language_proficiencies) return false;
    const proficiency = user.language_proficiencies.find(
      lp => lp.language_id === lang.id
    );
    if (!proficiency) return false;
    
    // Only include intermediate, fluent, and native
    const level = proficiency.proficiency_level.toLowerCase();
    return level === 'intermediate' || level === 'fluent' || level === 'native';
  });

  // Initialize all known languages as selected
  useEffect(() => {
    const initialSelection = new Set(knownLanguages.map(lang => lang.id));
    setSelectedKnownLanguages(initialSelection);
  }, [user, languages]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError('');

      let language_ids: string;
      
      if (searchDirection === 'current-to-known') {
        // Search in current language
        language_ids = selectedLanguage.id;
      } else {
        // Search in known languages
        language_ids = Array.from(selectedKnownLanguages).join(',');
      }

      const data = await wordService.search({
        q: searchQuery,
        language_ids,
        include_translations: true,
      });

      // Filter results based on search direction
      let filteredResults = data;
      if (searchDirection === 'current-to-known') {
        // Show only translations in known languages
        console.log('Known language IDs:', Array.from(selectedKnownLanguages));
        console.log('All translations:', data.map(w => w.translations));
        
        filteredResults = data.map(word => {
          const filteredTranslations = word.translations.filter(trans => {
            const isKnown = selectedKnownLanguages.has(trans.language_id);
            console.log(`Translation "${trans.word}" (${trans.language_id}) is known: ${isKnown}`);
            return isKnown;
          });
          
          return {
            ...word,
            translations: filteredTranslations,
          };
        });
      } else {
        // Show only translations in current language
        filteredResults = data.map(word => ({
          ...word,
          translations: word.translations.filter(trans =>
            trans.language_id === selectedLanguage.id
          ),
        }));
      }

      setResults(filteredResults);
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.response?.data?.detail || 'Failed to search words');
    } finally {
      setLoading(false);
    }
  };

  const toggleKnownLanguage = (languageId: string) => {
    const newSelection = new Set(selectedKnownLanguages);
    if (newSelection.has(languageId)) {
      newSelection.delete(languageId);
    } else {
      newSelection.add(languageId);
    }
    setSelectedKnownLanguages(newSelection);
  };

  const toggleSearchDirection = () => {
    setSearchDirection(prev =>
      prev === 'current-to-known' ? 'known-to-current' : 'current-to-known'
    );
    setResults([]); // Clear results when changing direction
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Group translations by language
  const groupTranslationsByLanguage = (translations: any[]) => {
    const grouped: { [key: string]: any[] } = {};
    translations.forEach(trans => {
      const langName = trans.language_name || 'Unknown';
      if (!grouped[langName]) {
        grouped[langName] = [];
      }
      grouped[langName].push(trans);
    });
    return grouped;
  };

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
          <button
            className="toggle-button"
            onClick={toggleSearchDirection}
          >
            <span className="toggle-label">Search direction:</span>
            <span className="toggle-value">
              {searchDirection === 'current-to-known' 
                ? `${selectedLanguage.name} → Known Languages`
                : `Known Languages → ${selectedLanguage.name}`}
            </span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 3.5a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V4a.5.5 0 0 1 .5-.5zM8 12.5a.5.5 0 0 1 .5.5v.5a.5.5 0 0 1-1 0v-.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M3.354 11.354a.5.5 0 0 1 0-.708l8-8a.5.5 0 0 1 .708.708l-8 8a.5.5 0 0 1-.708 0z"/>
            </svg>
          </button>
        </div>

        {knownLanguages.length > 0 && (
          <div className="language-filters">
            <span className="filter-label">Filter by known languages:</span>
            <div className="language-toggles">
              {knownLanguages.map(lang => (
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
            <p className="hint">Join languages with intermediate or higher proficiency to use the dictionary.</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="results-section">
          <h2 className="results-title">Results ({results.length})</h2>
          <div className="results-list">
            {results.map(word => (
              <div key={word.id} className="word-result-card">
                <div className="word-header">
                  <div className="word-info">
                    <h3 className="word-text">{word.word}</h3>
                    {word.romanization && (
                      <span className="word-romanization">({word.romanization})</span>
                    )}
                    {word.part_of_speech && (
                      <span className="word-pos">{word.part_of_speech}</span>
                    )}
                  </div>
                </div>

                {word.translations.length > 0 ? (
                  <div className="translations-section">
                    {Object.entries(groupTranslationsByLanguage(word.translations)).map(([langName, translations]) => (
                      <div key={langName} className="language-group">
                        <h4 className="language-name">{langName}</h4>
                        <div className="translations-list">
                          {translations.map((trans: any) => (
                            <div key={trans.id} className="translation-item">
                              <div className="translation-word">
                                <span className="trans-text">{trans.word}</span>
                                {trans.romanization && (
                                  <span className="trans-romanization">({trans.romanization})</span>
                                )}
                                {trans.part_of_speech && (
                                  <span className="trans-pos">{trans.part_of_speech}</span>
                                )}
                              </div>
                              {trans.notes && (
                                <div className="translation-notes">
                                  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                    <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                                  </svg>
                                  <span>{trans.notes}</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-translations">
                    No translations available in selected languages
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && searchQuery && results.length === 0 && !error && (
        <div className="no-results">
          <svg width="64" height="64" viewBox="0 0 16 16" fill="currentColor">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
          </svg>
          <p>No results found for "{searchQuery}"</p>
        </div>
      )}
    </div>
  );
}

