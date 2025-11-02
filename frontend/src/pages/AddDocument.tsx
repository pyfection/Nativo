import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import documentService, { CreateDocumentData } from '../services/documentService';
import languageService, { LanguageListItem } from '../services/languageService';
import './AddDocument.css';

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

export default function AddDocument() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [languages, setLanguages] = useState<LanguageListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<CreateDocumentData>({
    content: '',
    document_type: 'story',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchLanguages = async () => {
      try {
        const langs = await languageService.getAll();
        setLanguages(langs);
      } catch (err) {
        console.error('Failed to fetch languages:', err);
      }
    };

    fetchLanguages();
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await documentService.create(formData);
      navigate('/documents');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create document');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="add-document-page">
      <div className="page-header">
        <h1>Add New Document</h1>
        <p>Preserve texts and written content in endangered languages</p>
      </div>

      <form onSubmit={handleSubmit} className="document-form">
        {error && <div className="error-message">{error}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="document_type">Document Type *</label>
            <select
              id="document_type"
              name="document_type"
              value={formData.document_type}
              onChange={handleChange}
              required
            >
              {DOCUMENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="language_id">Language</label>
            <select
              id="language_id"
              name="language_id"
              value={formData.language_id || ''}
              onChange={handleChange}
            >
              <option value="">Select a language (optional)</option>
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name} {lang.native_name && `(${lang.native_name})`}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="content">Content *</label>
          <textarea
            id="content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            required
            rows={10}
            placeholder="Enter the document content..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="source">Source</label>
          <input
            type="text"
            id="source"
            name="source"
            value={formData.source || ''}
            onChange={handleChange}
            placeholder="Origin or citation of this document"
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes || ''}
            onChange={handleChange}
            rows={3}
            placeholder="Internal notes or additional information"
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/documents')} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Document'}
          </button>
        </div>
      </form>
    </div>
  );
}

