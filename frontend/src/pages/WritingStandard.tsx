import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { Language } from '../App';
import { useUILanguage } from '../contexts/UILanguageContext';
import documentService from '../services/documentService';
import { DocumentWithTexts } from '../types/document';
import { Text, TextFormat } from '../types/text';
import './WritingStandard.css';

interface WritingStandardProps {
  selectedLanguage: Language;
  languages: Language[];
}

/**
 * /languages/:id/standard
 *
 * Renders the Document the admin has promoted as a language's writing
 * standard. The Document can have several Texts (translations of the rules);
 * we pick the most useful one for the current user — preferring the
 * language's own native rendition, then the UI language, then the primary
 * Text on the Document, then whatever's first.
 *
 * Markdown Texts (the common case for standards) render with GFM (tables +
 * task lists). Plain Texts render as preformatted text so line breaks and
 * indentation survive.
 */
export default function WritingStandard({
  selectedLanguage,
  languages,
}: WritingStandardProps) {
  const { id } = useParams<{ id: string }>();
  const { uiLanguage } = useUILanguage();

  const language = useMemo(
    () => languages.find((l) => l.id === id) ?? selectedLanguage,
    [languages, id, selectedLanguage],
  );

  const [doc, setDoc] = useState<DocumentWithTexts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTextId, setActiveTextId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setDoc(null);

    if (!language?.writingStandardDocumentId) {
      setLoading(false);
      return;
    }
    documentService
      .getById(language.writingStandardDocumentId)
      .then((d) => {
        if (cancelled) return;
        setDoc(d);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.response?.data?.detail || 'Failed to load the writing standard.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [language?.writingStandardDocumentId]);

  // Pick the best Text to display. Priority:
  //   1. Same language as the standard target (e.g. Bavarian standard in Bavarian)
  //   2. UI language (e.g. English overview of a Bavarian standard)
  //   3. Marked is_primary
  //   4. First text on the document
  const initialTextId = useMemo(() => {
    if (!doc || doc.texts.length === 0) return null;
    const inTargetLang = doc.texts.find((t) => t.language_id === language?.id);
    if (inTargetLang) return inTargetLang.id;
    const inUiLang = uiLanguage && doc.texts.find((t) => t.language_id === uiLanguage.id);
    if (inUiLang) return inUiLang.id;
    const primary = doc.texts.find((t) => t.is_primary);
    if (primary) return primary.id;
    return doc.texts[0].id;
  }, [doc, language?.id, uiLanguage]);

  useEffect(() => {
    if (initialTextId && activeTextId == null) setActiveTextId(initialTextId);
  }, [initialTextId, activeTextId]);

  const activeText: Text | undefined = useMemo(
    () => doc?.texts.find((t) => t.id === activeTextId),
    [doc, activeTextId],
  );

  if (loading) {
    return (
      <div className="writing-standard-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading the writing standard…</p>
        </div>
      </div>
    );
  }

  if (!language) {
    return (
      <div className="writing-standard-page">
        <div className="error-state">
          <p>Language not found.</p>
        </div>
      </div>
    );
  }

  if (!language.writingStandardDocumentId) {
    return (
      <div className="writing-standard-page">
        <header className="writing-standard-header">
          <h1 className="writing-standard-title">
            Writing standard · {language.name}
          </h1>
        </header>
        <div className="writing-standard-empty">
          <p>
            No writing standard has been published for <strong>{language.name}</strong>{' '}
            yet.
          </p>
          <p className="writing-standard-empty-hint">
            An admin can promote any Document to be this language's official
            standard from the Document detail page.
          </p>
          <Link to="/documents" className="btn btn-ghost">
            Browse documents
          </Link>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="writing-standard-page">
        <div className="error-state">
          <p>{error}</p>
          <Link to={`/languages`} className="btn btn-ghost">
            Back to languages
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="writing-standard-page">
      <header className="writing-standard-header">
        <p className="writing-standard-eyebrow">
          Writing standard
        </p>
        <h1 className="writing-standard-title">
          {language.name}
          <span className="writing-standard-native"> · {language.nativeName}</span>
        </h1>
        {doc && activeText?.title && (
          <p className="writing-standard-doc-title">{activeText.title}</p>
        )}
      </header>

      {/* If the Document has multiple Texts (e.g. Bavarian original + English
          overview), let the reader switch between them — same UX as the
          Document detail / linking sidebar. */}
      {doc && doc.texts.length > 1 && (
        <nav className="writing-standard-tabs">
          {doc.texts.map((t) => {
            const tLang = languages.find((l) => l.id === t.language_id);
            return (
              <button
                key={t.id}
                type="button"
                className={`writing-standard-tab ${
                  t.id === activeTextId ? 'active' : ''
                }`}
                onClick={() => setActiveTextId(t.id)}
                title={`Show this text${tLang ? ' (in ' + tLang.name + ')' : ''}`}
              >
                {t.title || (tLang ? tLang.name : 'Text')}
                {tLang && (
                  <span className="writing-standard-tab-lang">{tLang.name}</span>
                )}
              </button>
            );
          })}
        </nav>
      )}

      {activeText ? (
        <article className="writing-standard-body">
          {activeText.format === TextFormat.MARKDOWN ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {activeText.content}
            </ReactMarkdown>
          ) : (
            <pre className="writing-standard-plain">{activeText.content}</pre>
          )}
        </article>
      ) : (
        <p className="writing-standard-empty-hint">
          This standard document has no readable content yet.
        </p>
      )}

      <footer className="writing-standard-footer">
        <Link to={`/documents/${doc?.id}`} className="btn btn-ghost btn-sm">
          Open in document editor
        </Link>
      </footer>
    </div>
  );
}
