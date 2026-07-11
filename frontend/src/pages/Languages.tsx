import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import languageService, { LanguageResponse } from '../services/languageService';
import { useAuth } from '../contexts/AuthContext';
import LanguageCard from '../components/languages/LanguageCard';
import { languageDisplayName } from '../utils/languageName';
import './Languages.css';

export default function Languages() {
  const { t } = useTranslation();
  const { user, isAuthenticated, refreshUserProficiencies } = useAuth();
  const [languages, setLanguages] = useState<LanguageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'joined' | 'not-joined'>('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchLanguages();
  }, []);

  const fetchLanguages = async () => {
    try {
      setLoading(true);
      const data = await languageService.getAll();
      
      // Fetch details for each language to get full information
      const detailedLanguages = await Promise.all(
        data.map(lang => languageService.getById(lang.id))
      );
      
      setLanguages(detailedLanguages);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('languages_page.load_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageJoined = async () => {
    await refreshUserProficiencies();
  };

  // Filter languages
  const filteredLanguages = languages.filter((language) => {
    // Text search
    if (search) {
      const searchLower = search.toLowerCase();
      const matchesSearch =
        language.name.toLowerCase().includes(searchLower) ||
        languageDisplayName(language).toLowerCase().includes(searchLower) ||
        language.native_name?.toLowerCase().includes(searchLower) ||
        language.description?.toLowerCase().includes(searchLower);
      if (!matchesSearch) return false;
    }

    // Join status filter
    if (filter === 'joined') {
      return user?.language_proficiencies?.some(lp => lp.language_id === language.id);
    } else if (filter === 'not-joined') {
      return !user?.language_proficiencies?.some(lp => lp.language_id === language.id);
    }

    return true;
  });

  if (loading) {
    return (
      <div className="languages-page">
        <div className="loading-state">{t('languages_page.loading')}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="languages-page">
        <div className="error-state">{error}</div>
      </div>
    );
  }

  return (
    <div className="languages-page">
      <div className="page-header">
        <div>
          <h1>{t('languages_page.title')}</h1>
          <p>{t('languages_page.subtitle')}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-bar">
          <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
          </svg>
          <input
            type="text"
            placeholder={t('languages_page.search_placeholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="search-input"
          />
        </div>

        {/* Join-status tabs only make sense once you can join — hide for guests */}
        {isAuthenticated && (
          <div className="filter-tabs">
            <button
              className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              {t('languages_page.all_tab', { n: languages.length })}
            </button>
            <button
              className={`filter-tab ${filter === 'joined' ? 'active' : ''}`}
              onClick={() => setFilter('joined')}
            >
              {t('languages_page.joined_tab', { n: user?.language_proficiencies?.length || 0 })}
            </button>
            <button
              className={`filter-tab ${filter === 'not-joined' ? 'active' : ''}`}
              onClick={() => setFilter('not-joined')}
            >
              {t('languages_page.not_joined_tab', { n: languages.length - (user?.language_proficiencies?.length || 0) })}
            </button>
          </div>
        )}
      </div>

      {/* Languages Grid */}
      {filteredLanguages.length === 0 ? (
        <div className="empty-state">
          <p>{t('languages_page.no_results')}</p>
        </div>
      ) : (
        <div className="languages-grid">
          {filteredLanguages.map((language) => (
            <LanguageCard
              key={language.id}
              language={language}
              onLanguageJoined={handleLanguageJoined}
            />
          ))}
        </div>
      )}
    </div>
  );
}

