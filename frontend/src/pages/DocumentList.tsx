import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import documentService from '../services/documentService';
import { DocumentListItem } from '../types/document';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { languageDisplayName } from '../utils/languageName';
import './DocumentList.css';

interface DocumentListProps {
  selectedLanguage?: Language;
}

export default function DocumentList({ selectedLanguage }: DocumentListProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, canEditLanguage, canVerifyLanguage } = useAuth();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({ search: '' });

  // Check if user can edit this language
  const canEdit = selectedLanguage ? canEditLanguage(selectedLanguage.id) : false;
  const canVerify = selectedLanguage ? canVerifyLanguage(selectedLanguage.id) : false;

  useEffect(() => {
    fetchDocuments();
  }, [filters, selectedLanguage]);

  const fetchDocuments = async () => {
    if (!selectedLanguage) {
      setDocuments([]);
      return;
    }

    try {
      setLoading(true);
      const params: Record<string, string> = {
        language_id: selectedLanguage.id,
      };

      if (filters.search.trim()) {
        params.search_term = filters.search.trim();
      }

      const data = await documentService.getAll(params);
      setDocuments(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('docs_page.error_load'));
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const clearFilters = () => {
    setFilters({ search: '' });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (!selectedLanguage) {
    return (
      <div className="document-list-page">
        <div className="error-state">
          <p>{t('docs_page.select_language')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="document-list-page">
      <div className="page-header">
        <div>
          <h1>{t('docs_page.title')}</h1>
          <p>{t('docs_page.subtitle')}</p>
        </div>
        <div className="page-header-actions">
          {canVerify && (
            <button onClick={() => navigate('/review')} className="btn-secondary">
              {t('docs_page.review_queue')}
            </button>
          )}
          {isAuthenticated && (
            <button onClick={() => navigate('/documents/add')} className="btn-primary">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
              </svg>
              {canEdit ? t('docs_page.add_document') : t('docs_page.suggest_document')}
            </button>
          )}
        </div>
      </div>

      {!canEdit && selectedLanguage && (
        <div style={{ padding: '1rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '1rem' }}>
          <p style={{ margin: 0, color: '#856404' }}>
            {isAuthenticated ? (
              <>
                {t('docs_page.suggest_notice', { language: languageDisplayName(selectedLanguage) })}{' '}
                <Link to="/documents/add">{t('docs_page.suggest_link')}</Link>
              </>
            ) : (
              <>
                {t('docs_page.banner_pre', { language: languageDisplayName(selectedLanguage) })}{' '}
                <Link to="/register" state={{ from: location }}>{t('docs_page.banner_link')}</Link>{' '}
                {t('docs_page.banner_post')}
              </>
            )}
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters">
          <div className="filter-group search-group">
            <label htmlFor="search">{t('docs_page.search_label')}</label>
            <input
              type="text"
              id="search"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder={t('docs_page.search_placeholder')}
            />
          </div>

          {filters.search && (
            <button onClick={clearFilters} className="btn-clear-filters">
              {t('docs_page.clear_filters')}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>{t('docs_page.loading')}</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <h3>{t('docs_page.empty_title')}</h3>
          <p>{t('docs_page.empty_subtitle')}</p>
          <button onClick={() => navigate('/documents/add')} className="btn-primary">
            {t('docs_page.add_first_document')}
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="documents-table">
            <thead>
              <tr>
                <th>{t('docs_page.th_title')}</th>
                <th>{t('docs_page.th_content_preview')}</th>
                <th>{t('docs_page.th_source')}</th>
                <th>{t('docs_page.th_languages')}</th>
                <th>{t('docs_page.th_date')}</th>
                <th>{t('docs_page.th_actions')}</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="title-cell">{doc.title}</td>
                  <td className="content-cell">
                    {doc.content_preview}
                  </td>
                  <td className="source-cell">{doc.source || '—'}</td>
                  <td className="count-cell">{doc.text_count}</td>
                  <td className="date-cell">{formatDate(doc.created_at)}</td>
                  <td className="actions-cell">
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => navigate(`/documents/${doc.id}`)}
                      aria-label={t('docs_page.view_document')}
                      title={t('docs_page.view_document')}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    </button>
                    {canEdit && (
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => navigate(`/documents/${doc.id}/edit`)}
                        aria-label={t('docs_page.edit_document')}
                        title={t('docs_page.edit_document')}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" />
                        </svg>
                      </button>
                    )}
                    {canEdit && (
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => navigate(`/documents/${doc.id}/link`)}
                        aria-label={t('docs_page.link_words')}
                        title={t('docs_page.link_words')}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M10 13a5 5 0 0 1 7.54-.54l2 2a5 5 0 0 1-7.07 7.07l-1.29-1.3" />
                          <path d="M14 11a5 5 0 0 1-7.54.54l-2-2a5 5 0 0 1 7.07-7.07l1.29 1.3" />
                        </svg>
                      </button>
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

