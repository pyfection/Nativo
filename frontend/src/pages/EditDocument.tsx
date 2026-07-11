import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import documentService from '../services/documentService';
import { DocumentWithTexts } from '../types/document';
import { Text, TextUpdate, DocumentType, TextFormat } from '../types/text';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { DOCUMENT_TYPE_OPTIONS } from '../utils/documentTypes';
import { languageDisplayName } from '../utils/languageName';
import './EditDocument.css';

interface EditDocumentProps {
  selectedLanguage: Language;
  languages: Language[];
}

export default function EditDocument({ selectedLanguage, languages }: EditDocumentProps) {
  const { documentId } = useParams<{ documentId: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();
  const { t } = useTranslation();

  const [document, setDocument] = useState<DocumentWithTexts | null>(null);
  const [selectedTextId, setSelectedTextId] = useState<string>('');
  const [formData, setFormData] = useState<TextUpdate>({
    title: '',
    content: '',
    document_type: DocumentType.STORY,
    format: TextFormat.PLAIN,
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
        setError(err?.response?.data?.detail || t('edit_doc.load_failed'));
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId, t]);

  useEffect(() => {
    if (!document) return;

    const state = location.state as { textId?: string } | null;
    const queryTextId = searchParams.get('text');
    const preferredTextId = state?.textId ?? queryTextId ?? null;

    const preferred =
      document.texts.find((text) => text.id === preferredTextId) ??
      document.texts.find((text) => text.language_id === selectedLanguage.id) ??
      document.texts.find((text) => text.is_primary) ??
      document.texts[0];

    if (preferred) {
      setSelectedTextId(preferred.id);
      setFormData({
        title: preferred.title,
        content: preferred.content,
        document_type: preferred.document_type,
        format: preferred.format ?? TextFormat.PLAIN,
        source: preferred.source,
        notes: preferred.notes,
        learning_order: preferred.learning_order ?? null,
      });
    }
  }, [document, location.state, searchParams, selectedLanguage.id]);

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
      format: text.format ?? TextFormat.PLAIN,
      source: text.source,
      notes: text.notes,
      learning_order: text.learning_order ?? null,
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
      [name]:
        name === 'document_type'
          ? (value as DocumentType)
          : name === 'format'
            ? (value as TextFormat)
            : name === 'learning_order'
              ? value === ''
                ? null
                : Number(value)
              : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!documentId || !selectedTextId) return;
    if (!canEdit) {
      setError(t('edit_doc.no_permission'));
      return;
    }

    const payload: TextUpdate = {
      title: formData.title?.trim(),
      content: formData.content,
      document_type: formData.document_type,
      format: formData.format,
      source: formData.source?.trim() || undefined,
      notes: formData.notes?.trim() || undefined,
      learning_order: formData.learning_order ?? null,
    };

    try {
      setSaving(true);
      setError('');
      await documentService.updateText(documentId, selectedTextId, payload);
      setSuccess(t('edit_doc.update_success'));
      navigate(`/documents/${documentId}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item: { msg?: string }) => item?.msg).filter(Boolean).join(', ')
        : detail;
      setError(message || t('edit_doc.update_failed'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="edit-document-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>{t('edit_doc.loading')}</p>
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
            {t('edit_doc.back_to_document')}
          </button>
        </div>
      </div>
    );
  }

  if (!document || !selectedText) {
    return (
      <div className="edit-document-page">
        <div className="empty-state">
          <h3>{t('edit_doc.not_found')}</h3>
          <button className="btn-primary" onClick={handleBack}>
            {t('edit_doc.return_to_documents')}
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
            ← {t('edit_doc.back_to_document')}
          </button>
          <h1>{t('edit_doc.title')}</h1>
          <p className="page-subtitle">
            {selectedLanguageInfo
              ? `${languageDisplayName(selectedLanguageInfo)}${
                  selectedLanguageInfo.nativeName ? ` (${selectedLanguageInfo.nativeName})` : ''
                }`
              : t('edit_doc.unknown_language')}{' '}
            · {t(`edit_doc.type_${selectedText.document_type}`)}
          </p>
        </div>
        <div className="language-availability">
          <span className="language-availability-label">
            {t('edit_doc.available_in_languages', { count: document.texts.length })}
          </span>
          <div className="language-availability-list">
            {document.texts.map((text) => {
              const language = text.language_id
                ? languageMap.get(text.language_id.toString())
                : undefined;
              return (
                <button
                  key={text.id}
                  type="button"
                  className={`language-pill ${text.id === selectedTextId ? 'active' : ''}`}
                  onClick={() => handleTextChange(text.id)}
                  disabled={!canEdit && text.id !== selectedTextId}
                >
                  {language
                    ? `${languageDisplayName(language)}${language.nativeName ? ` (${language.nativeName})` : ''}`
                    : text.title}
                  {text.is_primary ? ` • ${t('edit_doc.primary')}` : ''}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {!canEdit && (
        <div className="warning-banner">
          {t('edit_doc.no_permission_banner')}
        </div>
      )}

      <form className="edit-document-form" onSubmit={handleSubmit}>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="title">{t('edit_doc.title_label')}</label>
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
            <label htmlFor="document_type">{t('edit_doc.type_label')}</label>
            <select
              id="document_type"
              name="document_type"
              value={formData.document_type ?? DocumentType.STORY}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            >
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {t(`edit_doc.type_${option.value}`)}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label
              htmlFor="format"
              title={t('edit_doc.format_title')}
            >
              {t('edit_doc.format_label')}
            </label>
            <select
              id="format"
              name="format"
              value={formData.format ?? TextFormat.PLAIN}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            >
              <option value={TextFormat.PLAIN}>{t('edit_doc.format_plain')}</option>
              <option value={TextFormat.MARKDOWN}>{t('edit_doc.format_markdown')}</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="source">{t('edit_doc.source_label')}</label>
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
            <label htmlFor="notes">{t('edit_doc.notes_label')}</label>
            <textarea
              id="notes"
              name="notes"
              rows={3}
              value={formData.notes ?? ''}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            />
          </div>

          <div className="form-group">
            <label htmlFor="learning_order">{t('edit_doc.learning_order_label')}</label>
            <input
              id="learning_order"
              name="learning_order"
              type="number"
              min={1}
              placeholder={t('edit_doc.learning_order_placeholder')}
              title={t('edit_doc.learning_order_title')}
              value={formData.learning_order ?? ''}
              onChange={handleFieldChange}
              disabled={!canEdit || saving}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="content">{t('edit_doc.content_label')}</label>
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
            {t('edit_doc.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={!canEdit || saving}>
            {saving ? t('edit_doc.saving') : t('edit_doc.save_changes')}
          </button>
        </div>
      </form>
    </div>
  );
}
