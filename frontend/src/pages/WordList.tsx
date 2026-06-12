import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import wordService, { WordListItem } from '../services/wordService';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import './WordList.css';

interface WordListProps {
  selectedLanguage?: Language;
}

export default function WordList({ selectedLanguage }: WordListProps) {
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();
  const [words, setWords] = useState<WordListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [filters, setFilters] = useState({
    status_filter: '',
    part_of_speech: '',
    search: '',
  });

  // Check if user can edit this language
  const canEdit = selectedLanguage ? canEditLanguage(selectedLanguage.id) : false;

  useEffect(() => {
    fetchWords();
  }, [filters, selectedLanguage]);

  const fetchWords = async () => {
    try {
      setLoading(true);
      const params: any = {};

      if (selectedLanguage) {
        params.language_id = selectedLanguage.id;
      }

      if (filters.status_filter) {
        params.status_filter = filters.status_filter;
      } else {
        params.include_all_statuses = true;
      }

      const data = await wordService.getAll(params);

      // Client-side filter on lemma + POS.
      let filtered = data;
      if (filters.part_of_speech) {
        filtered = filtered.filter((w) => w.part_of_speech === filters.part_of_speech);
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        filtered = filtered.filter((w) => w.lemma.toLowerCase().includes(q));
      }

      setWords(filtered);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load words');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const clearFilters = () => {
    setFilters({
      status_filter: '',
      part_of_speech: '',
      search: '',
    });
  };

  return (
    <div className="word-list-page">
      <div className="page-header">
        <div>
          <h1>Words</h1>
          <p>Browse and manage vocabulary entries</p>
        </div>
        {canEdit && (
          <button onClick={() => navigate('/words/add')} className="btn-primary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
            </svg>
            Add Word
          </button>
        )}
      </div>

      {!canEdit && selectedLanguage && (
        <div style={{ padding: '1rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '1rem' }}>
          <p style={{ margin: 0, color: '#856404' }}>
            You don't have permission to add words to this language. Contact an administrator to request access.
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters">
          <div className="filter-group search-group">
            <label htmlFor="search">Search</label>
            <input
              type="text"
              id="search"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder="Search words, definitions, romanization..."
            />
          </div>

          <div className="filter-group">
            <label htmlFor="part_of_speech">Part of Speech</label>
            <select
              id="part_of_speech"
              name="part_of_speech"
              value={filters.part_of_speech}
              onChange={handleFilterChange}
            >
              <option value="">All</option>
              <option value="noun">Noun</option>
              <option value="verb">Verb</option>
              <option value="adjective">Adjective</option>
              <option value="adverb">Adverb</option>
              <option value="pronoun">Pronoun</option>
              <option value="preposition">Preposition</option>
              <option value="conjunction">Conjunction</option>
              <option value="interjection">Interjection</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="status_filter">Status</label>
            <select
              id="status_filter"
              name="status_filter"
              value={filters.status_filter}
              onChange={handleFilterChange}
            >
              <option value="">All</option>
              <option value="draft">Draft</option>
              <option value="pending_review">Pending Review</option>
              <option value="published">Published</option>
            </select>
          </div>

          {(filters.search || filters.part_of_speech || filters.status_filter) && (
            <button onClick={clearFilters} className="btn-clear-filters">
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading words...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
        </div>
      ) : words.length === 0 ? (
        <div className="empty-state">
          <h3>No words found</h3>
          <p>Start by adding your first word to the collection</p>
          <button onClick={() => navigate('/words/add')} className="btn-primary">
            Add First Word
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="words-table">
            <thead>
              <tr>
                <th>Lemma</th>
                <th>Part of Speech</th>
                <th>Status</th>
                <th>Verified</th>
              </tr>
            </thead>
            <tbody>
              {words.map((word) => (
                <tr key={word.id} onClick={() => navigate(`/words/${word.id}`)} className="clickable-row">
                  <td className="word-cell">{word.lemma}</td>
                  <td className="pos-cell">{word.part_of_speech || '—'}</td>
                  <td>
                    <span className={`status-badge status-${word.status}`}>
                      {word.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="verified-cell">
                    {word.is_verified ? (
                      <span className="verified-badge">✓</span>
                    ) : (
                      <span className="unverified-badge">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
