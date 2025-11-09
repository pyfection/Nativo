import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import documentService from '../services/documentService';
import { DocumentListItem } from '../types/document';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import './DocumentList.css';

interface DocumentListProps {
  selectedLanguage?: Language;
}

export default function DocumentList({ selectedLanguage }: DocumentListProps) {
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({ search: '' });

  // Check if user can edit this language
  const canEdit = selectedLanguage ? canEditLanguage(selectedLanguage.id) : false;

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
      setError(err.response?.data?.detail || 'Failed to load documents');
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
          <p>Please select a language to view documents.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="document-list-page">
      <div className="page-header">
        <div>
          <h1>Documents</h1>
          <p>Browse and manage text documents and content</p>
        </div>
        {canEdit && (
          <button onClick={() => navigate('/documents/add')} className="btn-primary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
            </svg>
            Add Document
          </button>
        )}
      </div>

      {!canEdit && selectedLanguage && (
        <div style={{ padding: '1rem', backgroundColor: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '1rem' }}>
          <p style={{ margin: 0, color: '#856404' }}>
            You don't have permission to add documents to this language. Contact an administrator to request access.
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
              placeholder="Search title or content..."
            />
          </div>

          {filters.search && (
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
          <p>Loading documents...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="empty-state">
          <h3>No documents found</h3>
          <p>Start by adding your first document to the collection</p>
          <button onClick={() => navigate('/documents/add')} className="btn-primary">
            Add First Document
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="documents-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Content Preview</th>
                <th>Translations</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} onClick={() => navigate(`/documents/${doc.id}`)} className="clickable-row">
                  <td className="title-cell">{doc.title}</td>
                  <td className="content-cell">
                    {doc.content_preview}
                  </td>
                  <td className="count-cell">{doc.text_count}</td>
                  <td className="date-cell">{formatDate(doc.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

