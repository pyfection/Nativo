import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import wordService, { WordListItem } from '../services/wordService';
import languageService, { LanguageListItem } from '../services/languageService';
import './WordList.css';

export default function WordList() {
  const navigate = useNavigate();
  const [words, setWords] = useState<WordListItem[]>([]);
  const [languages, setLanguages] = useState<LanguageListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({
    language_id: '',
    status_filter: '',
  });

  useEffect(() => {
    fetchLanguages();
  }, []);

  useEffect(() => {
    fetchWords();
  }, [filters]);

  const fetchLanguages = async () => {
    try {
      const langs = await languageService.getAll();
      setLanguages(langs);
    } catch (err) {
      console.error('Failed to fetch languages:', err);
    }
  };

  const fetchWords = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filters.language_id) params.language_id = filters.language_id;
      if (filters.status_filter) params.status_filter = filters.status_filter;
      
      const data = await wordService.getAll(params);
      setWords(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load words');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const clearFilters = () => {
    setFilters({
      language_id: '',
      status_filter: '',
    });
  };

  return (
    <div className="word-list-page">
      <div className="page-header">
        <div>
          <h1>Words</h1>
          <p>Browse and manage vocabulary entries</p>
        </div>
        <button onClick={() => navigate('/words/add')} className="btn-primary">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
          </svg>
          Add Word
        </button>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="filters">
          <div className="filter-group">
            <label htmlFor="language_id">Language</label>
            <select
              id="language_id"
              name="language_id"
              value={filters.language_id}
              onChange={handleFilterChange}
            >
              <option value="">All Languages</option>
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name}
                </option>
              ))}
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
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="pending_review">Pending Review</option>
              <option value="published">Published</option>
            </select>
          </div>

          {(filters.language_id || filters.status_filter) && (
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
                <th>Word</th>
                <th>Part of Speech</th>
                <th>Definition</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {words.map((word) => (
                <tr key={word.id} onClick={() => navigate(`/words/${word.id}`)} className="clickable-row">
                  <td className="word-cell">{word.word}</td>
                  <td className="pos-cell">{word.part_of_speech || '—'}</td>
                  <td className="definition-cell">{word.definition}</td>
                  <td>
                    <span className={`status-badge status-${word.status}`}>
                      {word.status.replace('_', ' ')}
                    </span>
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

