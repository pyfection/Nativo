import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import documentService from '../services/documentService';
import { DocumentWithTexts } from '../types/document';
import { Text } from '../types/text';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { getDocumentTypeLabel } from '../utils/documentTypes';
import './DocumentDetail.css';

interface DocumentDetailProps {
  selectedLanguage: Language;
  languages: Language[];
}

export default function DocumentDetail({ selectedLanguage, languages }: DocumentDetailProps) {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();

  const [document, setDocument] = useState<DocumentWithTexts | null>(null);
  const [activeTextId, setActiveTextId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

    const preferred =
      document.texts.find((text) => text.language_id === selectedLanguage.id) || null;
    const primary = document.texts.find((text) => text.is_primary) || null;
    const first = document.texts[0] ?? null;

    setActiveTextId((prev) => {
      if (prev && document.texts.some((text) => text.id === prev)) {
        return prev;
      }
      return (preferred || primary || first)?.id ?? null;
    });
  }, [document, selectedLanguage.id]);

  const activeText: Text | undefined = document?.texts.find((text) => text.id === activeTextId);

  const canEdit =
    !!activeText?.language_id && canEditLanguage(activeText.language_id.toString());

  const handleBack = () => {
    navigate('/documents');
  };

  const handleEdit = () => {
    if (!documentId) return;
    const search = activeTextId ? `?text=${activeTextId}` : '';
    navigate(`/documents/${documentId}/edit${search}`);
  };

  if (loading) {
    return (
      <div className="document-detail-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="document-detail-page">
        <div className="error-state">
          <p>{error}</p>
          <button className="btn-secondary" onClick={handleBack}>
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="document-detail-page">
        <div className="empty-state">
          <h3>Document not found</h3>
          <button className="btn-primary" onClick={handleBack}>
            Return to Documents
          </button>
        </div>
      </div>
    );
  }

  if (!activeText) {
    return (
      <div className="document-detail-page">
        <div className="empty-state">
          <h3>This document has no texts yet</h3>
          <p>Add a translation to start working with this document.</p>
          <button className="btn-secondary" onClick={handleBack}>
            Back to Documents
          </button>
        </div>
      </div>
    );
  }

  const textLanguage = activeText.language_id
    ? languageMap.get(activeText.language_id.toString())
    : undefined;

  const createdAt = new Date(document.created_at).toLocaleString();
  const updatedAt = new Date(document.updated_at).toLocaleString();

  return (
    <div className="document-detail-page">
      <div className="document-header">
        <div>
          <button className="btn-link" onClick={handleBack}>
            ← Back to Documents
          </button>
          <h1>{activeText.title}</h1>
          <p className="document-subtitle">
            {textLanguage
              ? `${textLanguage.name}${
                  textLanguage.nativeName ? ` (${textLanguage.nativeName})` : ''
                }`
              : 'Unknown Language'}{' '}
            · {getDocumentTypeLabel(activeText.document_type)} · {document.texts.length}{' '}
            translation{document.texts.length === 1 ? '' : 's'}
          </p>
        </div>
        <div className="document-header-actions">
          <button className="btn-secondary" onClick={handleBack}>
            Back
          </button>
          {canEdit && (
            <button className="btn-primary" onClick={handleEdit}>
              Edit Document
            </button>
          )}
        </div>
      </div>

      <div className="document-content-grid">
        <aside className="document-sidebar">
          <h2>Translations</h2>
          <ul className="translation-list">
            {document.texts.map((text) => {
              const language = text.language_id
                ? languageMap.get(text.language_id.toString())
                : undefined;
              return (
                <li key={text.id}>
                  <button
                    type="button"
                    className={`translation-button ${text.id === activeTextId ? 'active' : ''}`}
                    onClick={() => setActiveTextId(text.id)}
                  >
                    <span className="translation-title">{text.title}</span>
                    <span className="translation-meta">
                      {language
                        ? `${language.name}${
                            language.nativeName ? ` (${language.nativeName})` : ''
                          }`
                        : 'Unknown'}
                      {text.is_primary ? ' · Primary' : ''}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <article className="document-content">
          <div className="document-meta">
            <div>
              <span className="meta-label">Document Type</span>
              <span className="meta-value">{getDocumentTypeLabel(activeText.document_type)}</span>
            </div>
            {activeText.source && (
              <div>
                <span className="meta-label">Source</span>
                <span className="meta-value">{activeText.source}</span>
              </div>
            )}
            {activeText.notes && (
              <div>
                <span className="meta-label">Notes</span>
                <span className="meta-value">{activeText.notes}</span>
              </div>
            )}
            <div>
              <span className="meta-label">Created</span>
              <span className="meta-value">{createdAt}</span>
            </div>
            <div>
              <span className="meta-label">Last Updated</span>
              <span className="meta-value">{updatedAt}</span>
            </div>
          </div>
          <div className="document-body">
            {activeText.content.split('\n').map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}


