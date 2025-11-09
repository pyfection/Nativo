import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import documentService from '../services/documentService';
import { DocumentWithTexts } from '../types/document';
import { Text, TextUpdate, DocumentType } from '../types/text';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { DOCUMENT_TYPE_OPTIONS, getDocumentTypeLabel } from '../utils/documentTypes';
import './EditDocument.css';

interface EditDocumentProps {
  selectedLanguage: Language;
  languages: Language[];
}

export default function EditDocument({ selectedLanguage, languages }: EditDocumentProps) {
  const { documentId } = useParams<{ documentId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();

  const [document, setDocument] = useState<DocumentWithTexts | null>(null);
  const [selectedTextId, setSelectedTextId] = useState<string>('');
  const [formData, setFormData] = useState<TextUpdate>({
    title: '',
    content: '',
    document_type: DocumentType.STORY,
    source: '',
    notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const languageMap = useMemo(
    () => new Map(languages.map((language) => [language.id, language])),
    [languages]
  );

  useEffect(() => {
    if (!documentId) return;

    const fetchDocument = async () => {
      try {
        setLoading(true);
        const data = await documentService.getById(documentId);
        setDocument(data);
        setError('');
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load document');
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  useEffect(() => {
    if (!document) return;

    const queryTextId = searchParams.get('text');
    const preferred =
      document.texts.find((text) => text.id === queryTextId) ??
      document.texts.find((text) => text.language_id === selectedLanguage.id) ??
      document.texts.find((text) => text.is_primary) ??
      document.texts[0];

    if (preferred) {
      setSelectedTextId(preferred.id);
      setFormData({
        title: preferred.title,
        content: preferred.content,
        document_type: preferred.document_type,
        source: preferred.source,
        notes: preferred.notes,
      });
    }
  }, [document, searchParams, selectedLanguage.id]);

  const selectedText: Text | undefined = document?.texts.find(
    (text) => text.id === selectedTextId
  );

  const canEdit =
    !!selectedText?.language_id && canEditLanguage(selectedText.language_id.toString());

  const handleBack = () => {
    if (documentId) {
      navigate(`/documents/${documentId}`);
    } else {
      navigate('/documents');
    }
  };

  const handleTextChange = (textId: string) => {
    const text = document?.texts.find((item) => item.id === textId);
    if (!text) return;

    setSelectedTextId(textId);
    setFormData({
      title: text.title,
      content: text.content,
      document_type: text.document_type,
      source: text.source,
      notes: text.notes,
    });
    setSuccess('');
    setError('');
  };

  const handleFieldChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'document_type' ? (value as DocumentType) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!documentId || !selectedTextId) return;
    if (!canEdit) {
      setError('You do not have permission to edit this translation.');
      return;
    }

    const payload: TextUpdate = {
      title: formData.title?.trim(),
      content: formData.content,
      document_type: formData.document_type,
      source: formData.source?.trim() || undefined,
      notes: formData.notes?.trim() || undefined,
    };

    try {
      setSaving(true);
      setError('');
      await documentService.updateText(documentId, selectedTextId, payload);
      setSuccess('Document updated successfully.');
      navigate(`/documents/${documentId}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item: { msg?: string }) => item?.msg).filter(Boolean).join(', ')
        : detail;
      setError(message || 'Failed to update document');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="edit-document-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  if (error && !document) {
    return (
      <div className="edit-document-page">
        <div className="error-state">
          <p>{error}</p>
          <button onClick={handleBack} className="btn-secondary">
            Back to Document
          </button>
        </div>
      </div>
    );
  }

  if (!document || !selectedText) {
    return (
      <div className="edit-document-page">
        <div className="empty-state">
          <h3>Document not found</h3>
          <button className="btn-primary" onClick={handleBack}>
            Return to Documents
          </button>
        </div>
      </div>
    );
  }

  const selectedLanguageInfo = selectedText.language_id
    ? languageMap.get(selectedText.language_id.toString())
    : undefined;

  return (
    <div className="edit-document-page">
      <div className="page-header">
        <div>
          <button className="btn-link" onClick={handleBack}>
            ← Back to Document
          </button>
          <h1>Edit Document</h1>
          <p className="page-subtitle">
            {selectedLanguageInfo
              ? `${selectedLanguageInfo.name}${
                  selectedLanguageInfo.nativeName ? ` (${selectedLanguageInfo.nativeName})` : ''
                }`
              : 'Unknown Language'}{' '}
            · {getDocumentTypeLabel(selectedText.document_type)}
          </p>
        </div>
        <div className="translation-switcher">
          <label htmlFor="translation-select">Editing translation</label>
          <select
            id="translation-select"
            value={selectedTextId}
            onChange={(e) => handleTextChange(e.target.value)}
          >
            {document.texts.map((text) => {
              const language = text.language_id
                ? languageMap.get(text.language_id.toString())
                : undefined;
              return (
                <option key={text.id} value={text.id}>
                  {text.title} —{' '}
                  {language
                    ? `${language.name}${
                        language.nativeName ? ` (${language.nativeName})` : ''
                      }`
                    : 'Unknown'}
                  {text.is_primary ? ' (Primary)' : ''}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {!canEdit && (
        <div className="warning-banner">
          You don't have permission to edit this translation. Contact an administrator to request
          access.
        </div>
      )}

      <form className="edit-document-form" onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input
              id="title"
              name="title"
              type="text"
              required
              value={formData.title ?? ''}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            />
          </div>

          <div className="form-group">
            <label htmlFor="document_type">Document Type *</label>
            <select
              id="document_type"
              name="document_type"
              value={formData.document_type ?? DocumentType.STORY}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            >
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="source">Source</label>
            <input
              id="source"
              name="source"
              type="text"
              value={formData.source ?? ''}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            />
          </div>

          <div className="form-group">
            <label htmlFor="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              rows={3}
              value={formData.notes ?? ''}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="content">Content *</label>
          <textarea
            id="content"
            name="content"
            rows={12}
            required
            value={formData.content ?? ''}
            onChange={handleFieldChange}
            disabled={!canEdit || saving}
          />
        </div>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={handleBack} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={!canEdit || saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}


