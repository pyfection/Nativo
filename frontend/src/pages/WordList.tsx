import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import wordService, { WordListItem } from '../services/wordService';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { languageDisplayName } from '../utils/languageName';
import './WordList.css';

interface WordListProps {
  selectedLanguage?: Language;
}

export default function WordList({ selectedLanguage }: WordListProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, canEditLanguage, canVerifyLanguage } = useAuth();
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
  const canVerify = selectedLanguage ? canVerifyLanguage(selectedLanguage.id) : false;

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
      setError(err.response?.data?.detail || t('words_page.error_load'));
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
          <h1>{t('words_page.title')}</h1>
          <p>{t('words_page.subtitle')}</p>
        </div>
        <div className="page-header-actions">
        {canVerify && (
          <button onClick={() => navigate('/review')} className="btn-secondary">
            {t('words_page.review_queue')}
          </button>
        )}
        {canEdit && (
          <button onClick={() => navigate('/words/add')} className="btn-primary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
            </svg>
            {t('words_page.add_word')}
          </button>
        )}
        </div>
      </div>

      {!canEdit && selectedLanguage && (
        <div className="word-list-permission-notice">
          {isAuthenticated ? (
            <>
              {t('words_page.suggest_notice', { language: languageDisplayName(selectedLanguage) })}{' '}
              <Link to="/words/add">{t('words_page.suggest_link')}</Link>
            </>
          ) : (
            <>
              {t('words_page.banner_pre', { language: languageDisplayName(selectedLanguage) })}{' '}
              <Link to="/register" state={{ from: location }}>{t('words_page.banner_link')}</Link>{' '}
              {t('words_page.banner_post')}
            </>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters">
          <div className="filter-group search-group">
            <label htmlFor="search">{t('words_page.search_label')}</label>
            <input
              type="text"
              id="search"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder={t('words_page.search_placeholder')}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="part_of_speech">{t('words_page.pos_label')}</label>
            <select
              id="part_of_speech"
              name="part_of_speech"
              value={filters.part_of_speech}
              onChange={handleFilterChange}
            >
              <option value="">{t('words_page.filter_all')}</option>
              <option value="noun">{t('words_page.pos_noun')}</option>
              <option value="verb">{t('words_page.pos_verb')}</option>
              <option value="adjective">{t('words_page.pos_adjective')}</option>
              <option value="adverb">{t('words_page.pos_adverb')}</option>
              <option value="pronoun">{t('words_page.pos_pronoun')}</option>
              <option value="preposition">{t('words_page.pos_preposition')}</option>
              <option value="conjunction">{t('words_page.pos_conjunction')}</option>
              <option value="interjection">{t('words_page.pos_interjection')}</option>
              <option value="other">{t('words_page.pos_other')}</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="status_filter">{t('words_page.status_label')}</label>
            <select
              id="status_filter"
              name="status_filter"
              value={filters.status_filter}
              onChange={handleFilterChange}
            >
              <option value="">{t('words_page.filter_all')}</option>
              <option value="draft">{t('words_page.status_draft')}</option>
              <option value="pending_review">{t('words_page.status_pending_review')}</option>
              <option value="published">{t('words_page.status_published')}</option>
            </select>
          </div>

          {(filters.search || filters.part_of_speech || filters.status_filter) && (
            <button onClick={clearFilters} className="btn-clear-filters">
              {t('words_page.clear_filters')}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>{t('words_page.loading')}</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
        </div>
      ) : words.length === 0 ? (
        <div className="empty-state">
          <h3>{t('words_page.empty_title')}</h3>
          <p>{t('words_page.empty_subtitle')}</p>
          <button onClick={() => navigate('/words/add')} className="btn-primary">
            {t('words_page.add_first_word')}
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="words-table">
            <thead>
              <tr>
                <th>{t('words_page.th_lemma')}</th>
                <th>{t('words_page.pos_label')}</th>
                <th>{t('words_page.status_label')}</th>
                <th>{t('words_page.th_verified')}</th>
              </tr>
            </thead>
            <tbody>
              {words.map((word) => (
                <tr key={word.id} onClick={() => navigate(`/words/${word.id}`)} className="clickable-row">
                  <td className="word-cell">{word.lemma}</td>
                  <td className="pos-cell">
                    {word.part_of_speech
                      ? t(`words_page.pos_${word.part_of_speech}`, { defaultValue: word.part_of_speech })
                      : '—'}
                  </td>
                  <td>
                    <span className={`status-badge status-${word.status}`}>
                      {t(`words_page.status_${word.status}`, {
                        defaultValue: word.status.replace('_', ' '),
                      })}
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
