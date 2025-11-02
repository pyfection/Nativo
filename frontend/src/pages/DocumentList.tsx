import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import documentService, { Document } from '../services/documentService';
import { Language } from '../App';
import './DocumentList.css';

const DOCUMENT_TYPES = [
  { value: 'story', label: 'Story' },
  { value: 'historical_record', label: 'Historical Record' },
  { value: 'book', label: 'Book' },
  { value: 'article', label: 'Article' },
  { value: 'transcription', label: 'Transcription' },
  { value: 'definition', label: 'Definition' },
  { value: 'literal_translation', label: 'Literal Translation' },
  { value: 'context_note', label: 'Context Note' },
  { value: 'usage_example', label: 'Usage Example' },
  { value: 'etymology', label: 'Etymology' },
  { value: 'cultural_significance', label: 'Cultural Significance' },
  { value: 'translation', label: 'Translation' },
  { value: 'note', label: 'Note' },
  { value: 'other', label: 'Other' },
];

interface DocumentListProps {
  selectedLanguage?: Language;
}

export default function DocumentList({ selectedLanguage }: DocumentListProps) {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({
    document_type: '',
    search: '',
  });

  useEffect(() => {
    fetchDocuments();
  }, [filters, selectedLanguage]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params: any = {};
      
      // Always filter by selected language
      if (selectedLanguage) {
        params.language_id = selectedLanguage.id;
      }
      
      if (filters.document_type) params.document_type = filters.document_type;
      
      const data = await documentService.getAll(params);
      
      // Client-side search if needed
      let filtered = data;
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        filtered = data.filter(doc => 
          doc.content.toLowerCase().includes(searchLower) ||
          doc.source?.toLowerCase().includes(searchLower)
        );
      }
      
      setDocuments(filtered);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents');
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
      document_type: '',
      search: '',
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="document-list-page">
      <div className="page-header">
        <div>
          <h1>Documents</h1>
          <p>Browse and manage text documents and content</p>
        </div>
        <button onClick={() => navigate('/documents/add')} className="btn-primary">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
          </svg>
          Add Document
        </button>
      </div>

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
              placeholder="Search content, source..."
            />
          </div>

          <div className="filter-group">
            <label htmlFor="document_type">Type</label>
            <select
              id="document_type"
              name="document_type"
              value={filters.document_type}
              onChange={handleFilterChange}
            >
              <option value="">All Types</option>
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {(filters.search || filters.document_type) && (
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
                <th>Content Preview</th>
                <th>Type</th>
                <th>Source</th>
                <th>Notes</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} onClick={() => navigate(`/documents/${doc.id}`)} className="clickable-row">
                  <td className="content-cell">
                    {doc.content.length > 200 ? `${doc.content.substring(0, 200)}...` : doc.content}
                  </td>
                  <td>
                    <span className="type-badge">
                      {DOCUMENT_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type}
                    </span>
                  </td>
                  <td className="source-cell">{doc.source || '—'}</td>
                  <td className="notes-cell">{doc.notes || '—'}</td>
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

