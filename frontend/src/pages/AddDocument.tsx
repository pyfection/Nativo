import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import documentService, { CreateDocumentData } from '../services/documentService';
import { DOCUMENT_TYPE_OPTIONS } from '../utils/documentTypes';
import { DocumentType } from '../types/text';
import { Language } from '../App';
import './AddDocument.css';

interface AddDocumentProps {
  selectedLanguage: Language;
}

export default function AddDocument({ selectedLanguage }: AddDocumentProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<CreateDocumentData>({
    title: '',
    content: '',
    document_type: DocumentType.STORY,
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
      setError(message || t('add_doc.create_failed'));
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
        <h1>{t('add_doc.title')}</h1>
        <p>{t('add_doc.subtitle')}</p>
      </div>

      <form onSubmit={handleSubmit} className="document-form">
        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label htmlFor="document_type">{t('add_doc.type_label')}</label>
          <select
            id="document_type"
            name="document_type"
            value={formData.document_type}
            onChange={handleChange}
            required
          >
            {DOCUMENT_TYPE_OPTIONS.map((type) => (
              <option key={type.value} value={type.value}>
                {t(`add_doc.type_${type.value}`)}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="title">{t('add_doc.title_label')}</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder={t('add_doc.title_placeholder')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="content">{t('add_doc.content_label')}</label>
          <textarea
            id="content"
            name="content"
            value={formData.content}
            onChange={handleChange}
            required
            rows={10}
            placeholder={t('add_doc.content_placeholder')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="source">{t('add_doc.source_label')}</label>
          <input
            type="text"
            id="source"
            name="source"
            value={formData.source || ''}
            onChange={handleChange}
            placeholder={t('add_doc.source_placeholder')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">{t('add_doc.notes_label')}</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes || ''}
            onChange={handleChange}
            rows={3}
            placeholder={t('add_doc.notes_placeholder')}
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/documents')} className="btn-secondary">
            {t('add_doc.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t('add_doc.creating') : t('add_doc.create_document')}
          </button>
        </div>
      </form>
    </div>
  );
}
