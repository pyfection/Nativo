import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import documentService, { CreateDocumentData } from '../services/documentService';
import { DOCUMENT_TYPE_OPTIONS } from '../utils/documentTypes';
import { Language } from '../App';
import './AddDocument.css';

interface AddDocumentProps {
  selectedLanguage: Language;
}

export default function AddDocument({ selectedLanguage }: AddDocumentProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<CreateDocumentData>({
    title: '',
    content: '',
    document_type: 'story',
    language_id: selectedLanguage.id,
  });

  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      language_id: selectedLanguage.id,
    }));
  }, [selectedLanguage.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await documentService.create(formData);
      navigate('/documents');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item: { msg?: string }) => item?.msg).filter(Boolean).join(', ')
        : detail;
      setError(message || 'Failed to create document');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
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

        <div className="form-group">
          <label htmlFor="document_type">Document Type *</label>
          <select
            id="document_type"
            name="document_type"
            value={formData.document_type}
            onChange={handleChange}
            required
          >
            {DOCUMENT_TYPE_OPTIONS.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="Enter a title or short description"
          />
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

