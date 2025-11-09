import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import documentService from '../services/documentService';
import wordLinkService from '../services/wordLinkService';
import wordService, { CreateWordData, WordListItem } from '../services/wordService';
import { DocumentWithLinks } from '../types/document';
import {
  Text,
  TextWordLink,
  TextWordLinkCreate,
  TextWordLinkStatus,
} from '../types/text';
import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { getDocumentTypeLabel } from '../utils/documentTypes';
import './DocumentLinking.css';

type TokenStatus = TextWordLinkStatus | 'unlinked';

interface AnnotatedToken {
  id: string;
  text: string;
  start: number;
  end: number;
  type: 'word' | 'whitespace';
  status: TokenStatus;
  link?: TextWordLink;
}

interface SelectionState {
  start: number;
  end: number;
  text: string;
  link?: TextWordLink;
}

interface DocumentLinkingProps {
  selectedLanguage: Language;
  languages: Language[];
}

export default function DocumentLinking({ selectedLanguage, languages }: DocumentLinkingProps) {
  const { documentId } = useParams<{ documentId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();

  const [documentData, setDocumentData] = useState<DocumentWithLinks | null>(null);
  const [activeTextId, setActiveTextId] = useState<string | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<SelectionState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const [searchResults, setSearchResults] = useState<WordListItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const [showNewWordForm, setShowNewWordForm] = useState(false);
  const [newWordData, setNewWordData] = useState<CreateWordData>({
    word: '',
    language_id: selectedLanguage.id,
    definition: '',
  });

  const textContainerRef = useRef<HTMLDivElement | null>(null);
  const initialState = useMemo(() => {
    const state = location.state as { textId?: string } | null;
    return state?.textId;
  }, [location.state]);

  const languageMap = useMemo(
    () => new Map(languages.map((language) => [language.id, language])),
    [languages],
  );

  const fetchDocument = useCallback(
    async (withLoader = true) => {
      if (!documentId) return;
      try {
        if (withLoader) {
          setLoading(true);
        }
        setError(null);
        const data = await documentService.getWithLinks(documentId);
        setDocumentData(data);
        if (!activeTextId) {
          // Choose preferred text: initial state > selected language > primary > first
          const preferred =
            (initialState && data.texts.find((text) => text.id === initialState)) ||
            data.texts.find((text) => text.language_id === selectedLanguage.id) ||
            data.texts.find((text) => text.is_primary) ||
            data.texts[0] ||
            null;
          setActiveTextId(preferred?.id ?? null);
        } else if (!data.texts.some((text) => text.id === activeTextId)) {
          const fallback = data.texts[0] ?? null;
          setActiveTextId(fallback?.id ?? null);
        }
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load document for linking');
      } finally {
        if (withLoader) {
          setLoading(false);
        }
      }
    },
    [documentId, activeTextId, initialState, selectedLanguage.id],
  );

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  useEffect(() => {
    if (!actionMessage) return;
    const timer = setTimeout(() => setActionMessage(null), 3000);
    return () => clearTimeout(timer);
  }, [actionMessage]);

  useEffect(() => {
    if (!actionError) return;
    const timer = setTimeout(() => setActionError(null), 4000);
    return () => clearTimeout(timer);
  }, [actionError]);

  const activeText: Text | undefined = useMemo(() => {
    return documentData?.texts.find((text) => text.id === activeTextId);
  }, [documentData, activeTextId]);

  useEffect(() => {
    if (!activeText) {
      setSelectedSpan(null);
      return;
    }
    if (!activeText.language_id) {
      setSelectedSpan(null);
    }
    setNewWordData((prev) => ({
      ...prev,
      language_id: activeText.language_id ?? selectedLanguage.id,
    }));
  }, [activeText, selectedLanguage.id]);

  const canEdit = useMemo(() => {
    if (!activeText?.language_id) return false;
    return canEditLanguage(activeText.language_id.toString());
  }, [activeText?.language_id, canEditLanguage]);

  const tokens: AnnotatedToken[] = useMemo(() => {
    if (!activeText) return [];

    const content = activeText.content ?? '';
    const links = activeText.word_links ?? [];
    const linkMap = new Map<string, TextWordLink>();
    links.forEach((link) => {
      linkMap.set(`${link.start_char}-${link.end_char}`, link);
    });

    const annotated: AnnotatedToken[] = [];
    const tokenRegex = /\b[\w'-]+\b/g;
    let match: RegExpExecArray | null;
    let cursor = 0;

    while ((match = tokenRegex.exec(content)) !== null) {
      const start = match.index;
      const end = start + match[0].length;

      if (cursor < start) {
        const whitespaceText = content.slice(cursor, start);
        annotated.push({
          id: `ws-${cursor}`,
          text: whitespaceText,
          start: cursor,
          end: start,
          type: 'whitespace',
          status: 'unlinked',
        });
      }

      const key = `${start}-${end}`;
      const link = linkMap.get(key);
      annotated.push({
        id: `word-${start}-${end}`,
        text: match[0],
        start,
        end,
        type: 'word',
        status: link ? link.status : 'unlinked',
        link,
      });

      cursor = end;
    }

    if (cursor < content.length) {
      annotated.push({
        id: `ws-${cursor}`,
        text: content.slice(cursor),
        start: cursor,
        end: content.length,
        type: 'whitespace',
        status: 'unlinked',
      });
    }

    return annotated;
  }, [activeText]);

  const getOffsetFromNode = useCallback(
    (node: Node, nodeOffset: number): number | null => {
      const container = textContainerRef.current;
      if (!container) return null;

      const targetNode = node;
      if (!container.contains(targetNode)) {
        return null;
      }

      let element: HTMLElement | null =
        targetNode.nodeType === Node.TEXT_NODE
          ? (targetNode.parentElement as HTMLElement | null)
          : (targetNode as HTMLElement | null);

      if (!element) {
        return null;
      }

      const span = element.closest<HTMLSpanElement>('[data-start]');
      if (!span || span.dataset.start === undefined || span.dataset.end === undefined) {
        return null;
      }

      const spanStart = Number(span.dataset.start);
      const spanEnd = Number(span.dataset.end);

      let relativeOffset = 0;
      if (targetNode.nodeType === Node.TEXT_NODE) {
        const textContent = targetNode.textContent ?? '';
        const clamped = Math.min(Math.max(nodeOffset, 0), textContent.length);
        relativeOffset = clamped;
      } else {
        const spanLength = Math.max(spanEnd - spanStart, 0);
        relativeOffset = Math.min(Math.max(nodeOffset, 0), spanLength);
      }

      return spanStart + relativeOffset;
    },
    [],
  );

  const updateSelectionFromNative = useCallback(() => {
    const container = textContainerRef.current;
    if (!container || !activeText) return;

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
      setSelectedSpan(null);
      return;
    }

    const range = selection.getRangeAt(0);
    if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) {
      setSelectedSpan(null);
      return;
    }

    const startOffset = getOffsetFromNode(range.startContainer, range.startOffset);
    const endOffset = getOffsetFromNode(range.endContainer, range.endOffset);

    if (startOffset === null || endOffset === null) {
      setSelectedSpan(null);
      return;
    }

    const start = Math.min(startOffset, endOffset);
    const end = Math.max(startOffset, endOffset);

    if (start === end) {
      setSelectedSpan(null);
      return;
    }

    const snippet = activeText.content.slice(start, end);
    const linkMatch = activeText.word_links?.find(
      (link) => link.start_char === start && link.end_char === end,
    );

    setSelectedSpan({
      start,
      end,
      text: snippet,
      link: linkMatch,
    });
  }, [activeText, getOffsetFromNode]);

  const findNodeAtOffset = useCallback(
    (offset: number): { node: Node; offset: number } | null => {
      const container = textContainerRef.current;
      if (!container) return null;

      const spans = container.querySelectorAll<HTMLSpanElement>('[data-start]');
      for (const span of spans) {
        const spanStart = Number(span.dataset.start);
        const spanEnd = Number(span.dataset.end);
        if (Number.isNaN(spanStart) || Number.isNaN(spanEnd)) continue;

        if (offset >= spanStart && offset <= spanEnd) {
          const textNode = span.firstChild ?? span;
          const relative = Math.min(Math.max(offset - spanStart, 0), spanEnd - spanStart);
          return { node: textNode, offset: relative };
        }
      }
      return null;
    },
    [],
  );

  const selectRangeInText = useCallback(
    (start: number, end: number) => {
      const container = textContainerRef.current;
      if (!container) return;

      const selection = window.getSelection();
      if (!selection) return;

      const startInfo = findNodeAtOffset(start);
      const endInfo = findNodeAtOffset(end);
      if (!startInfo || !endInfo) return;

      const doc = window.document;
      const range = doc.createRange();
      range.setStart(startInfo.node, startInfo.offset);
      range.setEnd(endInfo.node, endInfo.offset);

      selection.removeAllRanges();
      selection.addRange(range);
    },
    [findNodeAtOffset],
  );

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.document === 'undefined') {
      return;
    }
    const doc = window.document;
    if (!doc) {
      return;
    }
    doc.addEventListener('selectionchange', updateSelectionFromNative);
    return () => {
      doc.removeEventListener('selectionchange', updateSelectionFromNative);
    };
  }, [updateSelectionFromNative]);

  useEffect(() => {
    const selection = window.getSelection();
    selection?.removeAllRanges();
    setSelectedSpan(null);
  }, [activeTextId]);

  const suggestions = useMemo(() => {
    return (activeText?.word_links ?? []).filter(
      (link) => link.status === TextWordLinkStatus.SUGGESTED,
    );
  }, [activeText?.word_links]);

  const applyLinkUpdate = useCallback((updatedLink: TextWordLink) => {
    setDocumentData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        texts: prev.texts.map((text) => {
          if (text.id !== updatedLink.text_id) {
            return text;
          }
          const currentLinks = text.word_links ?? [];
          const existingIndex = currentLinks.findIndex((link) => link.id === updatedLink.id);
          if (existingIndex >= 0) {
            const updatedLinks = [...currentLinks];
            updatedLinks[existingIndex] = updatedLink;
            return { ...text, word_links: updatedLinks };
          }
          return {
            ...text,
            word_links: [...currentLinks, updatedLink],
          };
        }),
      };
    });

    setSelectedSpan((prev) => {
      if (!prev) return prev;
      if (prev.start === updatedLink.start_char && prev.end === updatedLink.end_char) {
        return {
          ...prev,
          link: updatedLink,
        };
      }
      return prev;
    });
  }, []);

  const removeLinkFromState = useCallback((textId: string, linkId: string) => {
    setDocumentData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        texts: prev.texts.map((text) => {
          if (text.id !== textId) return text;
          const remaining = (text.word_links ?? []).filter((link) => link.id !== linkId);
          return { ...text, word_links: remaining };
        }),
      };
    });

    setSelectedSpan((prev) => {
      if (prev?.link?.id === linkId) {
        return {
          ...prev,
          link: undefined,
        };
      }
      return prev;
    });
  }, []);

  const handleLinkToWord = async (wordId: string) => {
    if (!activeText || !selectedSpan) return;
    setIsSaving(true);
    setActionError(null);
    try {
      const payload: TextWordLinkCreate = {
        word_id: wordId,
        start_char: selectedSpan.start,
        end_char: selectedSpan.end,
        status: TextWordLinkStatus.CONFIRMED,
      };
      const link = await wordLinkService.create(activeText.id, payload);
      applyLinkUpdate(link);
      setActionMessage('Link created successfully.');
      setSearchQuery('');
      setSearchResults([]);
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to create link');
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmLink = async (link: TextWordLink) => {
    if (!activeText) return;
    setIsSaving(true);
    setActionError(null);
    try {
      const updated = await wordLinkService.update(activeText.id, link.id, {
        status: TextWordLinkStatus.CONFIRMED,
      });
      applyLinkUpdate(updated);
      setActionMessage('Link confirmed.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to confirm link');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRejectLink = async (link: TextWordLink) => {
    if (!activeText) return;
    setIsSaving(true);
    setActionError(null);
    try {
      const updated = await wordLinkService.update(activeText.id, link.id, {
        status: TextWordLinkStatus.REJECTED,
      });
      applyLinkUpdate(updated);
      setActionMessage('Suggestion rejected.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to reject suggestion');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveLink = async (link: TextWordLink) => {
    if (!activeText) return;
    setIsSaving(true);
    setActionError(null);
    try {
      await wordLinkService.remove(activeText.id, link.id);
      removeLinkFromState(link.text_id, link.id);
      setActionMessage('Link removed.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to remove link');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerateSuggestionsForText = async () => {
    if (!activeText) return;
    setIsSuggesting(true);
    setActionError(null);
    try {
      await wordLinkService.regenerateSuggestions(activeText.id);
      await fetchDocument(false);
      setActionMessage('Suggestions regenerated for this text.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to regenerate suggestions');
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleRegenerateForDocument = async () => {
    if (!documentId) return;
    setIsSuggesting(true);
    setActionError(null);
    try {
      const data = await documentService.regenerateLinkSuggestions(documentId);
      setDocumentData(data);
      setActionMessage('Suggestions regenerated for all texts.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to regenerate document suggestions');
    } finally {
      setIsSuggesting(false);
    }
  };

  const runWordSearch = useCallback(async () => {
    if (!activeText?.language_id) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);
    try {
      const results = await wordService.search({
        q: '', // empty query to fetch closest matches (backend should handle)
        language_ids: activeText.language_id,
        include_translations: false,
        limit: 10,
      });
      setSearchResults(results);
    } catch (err) {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, [activeText?.language_id]);

  const handleCreateWordAndLink = async () => {
    if (!activeText || !selectedSpan) return;
    setIsSaving(true);
    setActionError(null);
    try {
      const wordPayload: CreateWordData = {
        ...newWordData,
        language_id: activeText.language_id ?? selectedLanguage.id,
      };
      const newWord = await wordService.create(wordPayload);
      await handleLinkToWord(newWord.id);
      setNewWordData({
        word: '',
        language_id: activeText.language_id ?? selectedLanguage.id,
        definition: '',
      });
      setShowNewWordForm(false);
      setActionMessage('Word created and linked.');
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to create and link word');
    } finally {
      setIsSaving(false);
    }
  };

  const formatLanguageDisplay = (text: Text | undefined) => {
    if (!text?.language_id) return 'Unknown language';
    const language = languageMap.get(text.language_id.toString());
    if (!language) return 'Unknown language';
    return `${language.name}${
      language.nativeName && language.nativeName !== language.name ? ` (${language.nativeName})` : ''
    }`;
  };

  const handleBackToDocument = () => {
    if (documentId) {
      navigate(`/documents/${documentId}`, { state: { textId: activeTextId } });
    } else {
      navigate('/documents');
    }
  };

  if (loading) {
    return (
      <div className="document-linking-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !documentData || !activeText) {
    return (
      <div className="document-linking-page">
        <div className="error-state">
          <p>{error || 'Document not available for linking.'}</p>
          <button className="btn-secondary" onClick={handleBackToDocument}>
            Back to Document
          </button>
        </div>
      </div>
    );
  }

  const activeLanguageDisplay = formatLanguageDisplay(activeText);
  const selectedStatus = selectedSpan?.link?.status ?? 'unlinked';

  return (
    <div className="document-linking-page">
      <div className="document-linking-header">
        <div>
          <button className="btn-link" onClick={handleBackToDocument}>
            ← Back to Document
          </button>
          <h1>Link Words · {activeText.title}</h1>
          <p className="document-linking-subtitle">
            {activeLanguageDisplay} · {getDocumentTypeLabel(activeText.document_type)}
          </p>
        </div>
        <div className="document-linking-actions">
          <button
            className="btn-secondary"
            onClick={handleRegenerateSuggestionsForText}
            disabled={!canEdit || isSuggesting}
          >
            {isSuggesting ? 'Rebuilding…' : 'Regenerate Text Suggestions'}
          </button>
          <button
            className="btn-secondary"
            onClick={handleRegenerateForDocument}
            disabled={!canEdit || isSuggesting}
          >
            {isSuggesting ? 'Working…' : 'Regenerate Document Suggestions'}
          </button>
        </div>
      </div>

      {!canEdit && (
        <div className="document-linking-info">
          You have read-only access for this language. Linking actions are disabled.
        </div>
      )}

      {actionError && <div className="document-linking-error">{actionError}</div>}
      {actionMessage && <div className="document-linking-message">{actionMessage}</div>}

      <div className="document-linking-grid">
        <aside className="document-linking-sidebar">
          <h2>Texts ({documentData.texts.length})</h2>
          <ul className="translation-list">
            {documentData.texts.map((text) => (
              <li key={text.id}>
                <button
                  type="button"
                  className={`translation-button ${text.id === activeTextId ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTextId(text.id);
                    setSelectedSpan(null);
                  }}
                >
                  <span className="translation-title">{text.title}</span>
                  <span className="translation-meta">
                    {formatLanguageDisplay(text)}
                    {text.is_primary ? ' · Primary' : ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="document-linking-content">
          <div className="token-legend">
            <span className="legend-chip legend-unlinked">Unlinked</span>
            <span className="legend-chip legend-suggested">Suggested</span>
            <span className="legend-chip legend-confirmed">Linked</span>
            <span className="legend-chip legend-rejected">Rejected</span>
          </div>
          <div
            ref={textContainerRef}
            className="linking-text-container"
            onMouseUp={updateSelectionFromNative}
          >
            {tokens.map((token) => (
              <span
                key={token.id}
                data-start={token.start}
                data-end={token.end}
                className={[
                  'linking-token',
                  token.type === 'whitespace' ? 'token-whitespace' : 'token-word',
                  `status-${token.status}`,
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                {token.text}
              </span>
            ))}
          </div>
        </main>

        <aside className="document-linking-panel">
          <section>
            <h2>Selection</h2>
            {selectedSpan ? (
              <>
                <div className="selection-preview">
                  <span className="selection-text">{selectedSpan.text}</span>
                  <span className={`selection-status status-${selectedStatus}`}>
                    {selectedSpan.link ? selectedSpan.link.status : 'unlinked'}
                  </span>
                </div>
                {selectedSpan.link ? (
                  <div className="selection-actions">
                    <div className="selection-meta">
                      <strong>Word:</strong>{' '}
                      {selectedSpan.link.word_text ?? `#${selectedSpan.link.word_id}`}
                    </div>
                    <div className="selection-buttons">
                      <button
                        className="btn-primary"
                        onClick={() => handleConfirmLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                      >
                        Confirm
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRejectLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                      >
                        Reject
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRemoveLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                      >
                        Unlink
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="selection-actions">
                    <p className="selection-help">
                      Link this selection to an existing word or create a new one.
                    </p>
                    <div className="link-existing">
                      <button
                        className="btn-secondary"
                        onClick={runWordSearch}
                        disabled={!canEdit || searchLoading}
                      >
                        {searchLoading ? 'Searching…' : 'Search existing words'}
                      </button>
                    </div>
                    <div className="search-results">
                      {searchLoading && <p>Searching…</p>}
                      {!searchLoading && searchResults.length === 0 && (
                        <p>No words found.</p>
                      )}
                      {searchResults.map((word) => (
                        <div key={word.id} className="search-result">
                          <div>
                            <strong>{word.word}</strong>
                            {word.definition && <div className="search-definition">{word.definition}</div>}
                          </div>
                          <button
                            className="btn-primary"
                            onClick={() => handleLinkToWord(word.id)}
                            disabled={!canEdit || isSaving}
                          >
                            Link
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="new-word-section">
                      {!showNewWordForm ? (
                        <button
                          className="btn-secondary"
                          onClick={() => setShowNewWordForm(true)}
                          disabled={!canEdit}
                        >
                          Create new word
                        </button>
                      ) : (
                        <div className="new-word-form">
                          <label htmlFor="new-word">Word *</label>
                          <input
                            id="new-word"
                            type="text"
                            value={newWordData.word}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, word: event.target.value }))
                            }
                            disabled={!canEdit}
                          />
                          <label htmlFor="new-word-definition">Definition *</label>
                          <textarea
                            id="new-word-definition"
                            rows={3}
                            value={newWordData.definition}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, definition: event.target.value }))
                            }
                            disabled={!canEdit}
                          />
                          <div className="new-word-actions">
                            <button
                              className="btn-primary"
                              onClick={handleCreateWordAndLink}
                              disabled={
                                !canEdit ||
                                isSaving ||
                                !newWordData.word.trim() ||
                                !newWordData.definition.trim()
                              }
                            >
                              Create & Link
                            </button>
                            <button
                              className="btn-secondary"
                              onClick={() => setShowNewWordForm(false)}
                              disabled={isSaving}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p>Highlight any portion of the document to review or manage its link.</p>
            )}
          </section>

          <section className="suggestions-section">
            <h2>Suggestions ({suggestions.length})</h2>
            {suggestions.length === 0 ? (
              <p>No suggestions available. Try regenerating to get new suggestions.</p>
            ) : (
              <ul className="suggestion-list">
                {suggestions.map((link) => (
                  <li key={link.id} className="suggestion-item">
                    <div className="suggestion-snippet">
                      <span>{activeText.content.slice(link.start_char, link.end_char)}</span>
                      <small>{link.word_text ?? `Word #${link.word_id}`}</small>
                    </div>
                    <div className="suggestion-actions">
                      <button
                        className="btn-secondary"
                        onClick={() => {
                          selectRangeInText(link.start_char, link.end_char);
                          setSelectedSpan({
                            start: link.start_char,
                            end: link.end_char,
                            text: activeText.content.slice(link.start_char, link.end_char),
                            link,
                          });
                        }}
                      >
                        Select
                      </button>
                      <button
                        className="btn-primary"
                        onClick={() => handleConfirmLink(link)}
                        disabled={!canEdit || isSaving}
                      >
                        Confirm
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRejectLink(link)}
                        disabled={!canEdit || isSaving}
                      >
                        Reject
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}


