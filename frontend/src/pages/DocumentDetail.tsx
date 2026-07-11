import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import documentService from '../services/documentService';
import languageService from '../services/languageService';
import { DocumentWithTexts } from '../types/document';
import { Text } from '../types/text';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { getDocumentTypeLabel } from '../utils/documentTypes';
import { languageDisplayName } from '../utils/languageName';
import './DocumentDetail.css';

interface DocumentDetailProps {
  selectedLanguage: Language;
  languages: Language[];
}

export default function DocumentDetail({ selectedLanguage, languages }: DocumentDetailProps) {
  const { t } = useTranslation();
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, canEditLanguage, isAdmin } = useAuth();
  // Local mirror so the button can flip immediately after a promote/demote
  // round-trip without waiting for the parent's languages prop to re-fetch.
  // Set is keyed by language_id; presence means "this language has THIS
  // document as its writing standard right now".
  const [languagesUsingThisStandard, setLanguagesUsingThisStandard] = useState<
    Set<string>
  >(new Set());
  const [savingStandard, setSavingStandard] = useState(false);

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
        // Seed the pinned-language set so the button shows the right label.
        setLanguagesUsingThisStandard(
          new Set(
            languages
              .filter((l) => l.writingStandardDocumentId === documentId)
              .map((l) => l.id),
          ),
        );
      } catch (err: any) {
        setError(err?.response?.data?.detail || t('doc_detail.error_load'));
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
    // languages intentionally not in deps — we only re-seed on doc id change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    navigate(`/documents/${documentId}/edit`, { state: { textId: activeTextId } });
  };

  const handleLink = () => {
    if (!documentId) return;
    navigate(`/documents/${documentId}/link`, { state: { textId: activeTextId } });
  };

  if (loading) {
    return (
      <div className="document-detail-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>{t('doc_detail.loading')}</p>
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
            {t('doc_detail.back_to_documents')}
          </button>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="document-detail-page">
        <div className="empty-state">
          <h3>{t('doc_detail.not_found')}</h3>
          <button className="btn-primary" onClick={handleBack}>
            {t('doc_detail.return_to_documents')}
          </button>
        </div>
      </div>
    );
  }

  if (!activeText) {
    return (
      <div className="document-detail-page">
        <div className="empty-state">
          <h3>{t('doc_detail.no_texts_title')}</h3>
          <p>{t('doc_detail.no_texts_subtitle')}</p>
          <button className="btn-secondary" onClick={handleBack}>
            {t('doc_detail.back_to_documents')}
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
            ← {t('doc_detail.back_to_documents')}
          </button>
          <h1>{activeText.title}</h1>
          <p className="document-subtitle">
            {textLanguage
              ? `${languageDisplayName(textLanguage)}${
                  textLanguage.nativeName ? ` (${textLanguage.nativeName})` : ''
                }`
              : t('doc_detail.unknown_language')}{' '}
            · {getDocumentTypeLabel(activeText.document_type)}
          </p>
        </div>
        <div className="document-header-actions">
          <button className="btn-secondary" onClick={handleBack}>
            {t('doc_detail.back')}
          </button>
          {canEdit && (
            <button className="btn-secondary" onClick={handleLink}>
              {t('doc_detail.link_words')}
            </button>
          )}
          {isAdmin && activeText?.language_id && documentId && (
            <button
              className="btn-secondary"
              disabled={savingStandard}
              title={
                languagesUsingThisStandard.has(activeText.language_id)
                  ? t('doc_detail.standard_remove_title')
                  : t('doc_detail.standard_promote_title')
              }
              onClick={async () => {
                if (!activeText.language_id) return;
                setSavingStandard(true);
                try {
                  const alreadyPinned = languagesUsingThisStandard.has(activeText.language_id);
                  await languageService.setWritingStandard(
                    activeText.language_id,
                    alreadyPinned ? null : documentId,
                  );
                  setLanguagesUsingThisStandard((prev) => {
                    const next = new Set(prev);
                    if (alreadyPinned) next.delete(activeText.language_id!);
                    else next.add(activeText.language_id!);
                    return next;
                  });
                } catch (err: any) {
                  alert(err.response?.data?.detail || t('doc_detail.error_update_standard'));
                } finally {
                  setSavingStandard(false);
                }
              }}
            >
              {languagesUsingThisStandard.has(activeText.language_id)
                ? `✓ ${t('doc_detail.standard_on')}`
                : `📖 ${t('doc_detail.standard_off')}`}
            </button>
          )}
          {canEdit && (
            <button className="btn-primary" onClick={handleEdit}>
              {t('doc_detail.edit_document')}
            </button>
          )}
        </div>
      </div>

      <div className="document-content-grid">
        <aside className="document-sidebar">
          <h2>{t('doc_detail.available_in', { count: document.texts.length })}</h2>
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
                        ? `${languageDisplayName(language)}${
                            language.nativeName ? ` (${language.nativeName})` : ''
                          }`
                        : t('doc_detail.unknown')}
                      {text.is_primary ? ` · ${t('doc_detail.primary')}` : ''}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          {/* A missing translation is a contribution opportunity — pitch the
              signup exactly there instead of hiding the gap from guests. */}
          {!isAuthenticated && (
            <p className="translation-guest-cta">
              {t('doc_detail.cta_pre')}{' '}
              <Link to="/register" state={{ from: location }}>
                {t('doc_detail.cta_link')}
              </Link>
              {t('doc_detail.cta_post')}
            </p>
          )}
        </aside>

        <article className="document-content">
          <div className="document-meta">
            <div>
              <span className="meta-label">{t('doc_detail.meta_document_type')}</span>
              <span className="meta-value">{getDocumentTypeLabel(activeText.document_type)}</span>
            </div>
            {activeText.source && (
              <div>
                <span className="meta-label">{t('doc_detail.meta_source')}</span>
                <span className="meta-value">{activeText.source}</span>
              </div>
            )}
            {activeText.notes && (
              <div>
                <span className="meta-label">{t('doc_detail.meta_notes')}</span>
                <span className="meta-value">{activeText.notes}</span>
              </div>
            )}
            <div>
              <span className="meta-label">{t('doc_detail.meta_created')}</span>
              <span className="meta-value">{createdAt}</span>
            </div>
            <div>
              <span className="meta-label">{t('doc_detail.meta_last_updated')}</span>
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
