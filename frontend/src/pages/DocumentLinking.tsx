import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import documentService from '../services/documentService';
import wordLinkService from '../services/wordLinkService';
import wordService, {
  CreateLexemeData,
  LexemeWithForms,
  TranslationLink,
} from '../services/wordService';
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

const LETTER_REGEX =
  (() => {
    try {
      return new RegExp('\\p{L}', 'u');
    } catch {
      return /[A-Za-z]/;
    }
  })();

const PART_OF_SPEECH_OPTIONS = [
  { value: 'noun', label: 'Noun' },
  { value: 'verb', label: 'Verb' },
  { value: 'adjective', label: 'Adjective' },
  { value: 'adverb', label: 'Adverb' },
  { value: 'pronoun', label: 'Pronoun' },
  { value: 'preposition', label: 'Preposition' },
  { value: 'conjunction', label: 'Conjunction' },
  { value: 'interjection', label: 'Interjection' },
  { value: 'article', label: 'Article' },
  { value: 'determiner', label: 'Determiner' },
  { value: 'particle', label: 'Particle' },
  { value: 'numeral', label: 'Numeral' },
  { value: 'classifier', label: 'Classifier' },
  { value: 'other', label: 'Other' },
];

const GENDER_OPTIONS = [
  { value: 'masculine', label: 'Masculine' },
  { value: 'feminine', label: 'Feminine' },
  { value: 'neuter', label: 'Neuter' },
  { value: 'common', label: 'Common' },
  { value: 'animate', label: 'Animate' },
  { value: 'inanimate', label: 'Inanimate' },
  { value: 'not_applicable', label: 'Not applicable' },
];

const PLURALITY_OPTIONS = [
  { value: 'singular', label: 'Singular' },
  { value: 'plural', label: 'Plural' },
  { value: 'dual', label: 'Dual' },
  { value: 'trial', label: 'Trial' },
  { value: 'paucal', label: 'Paucal' },
  { value: 'collective', label: 'Collective' },
  { value: 'not_applicable', label: 'Not applicable' },
];

const CASE_OPTIONS = [
  { value: 'nominative', label: 'Nominative' },
  { value: 'accusative', label: 'Accusative' },
  { value: 'genitive', label: 'Genitive' },
  { value: 'dative', label: 'Dative' },
  { value: 'ablative', label: 'Ablative' },
  { value: 'locative', label: 'Locative' },
  { value: 'instrumental', label: 'Instrumental' },
  { value: 'vocative', label: 'Vocative' },
  { value: 'partitive', label: 'Partitive' },
  { value: 'comitative', label: 'Comitative' },
  { value: 'essive', label: 'Essive' },
  { value: 'translative', label: 'Translative' },
  { value: 'ergative', label: 'Ergative' },
  { value: 'absolutive', label: 'Absolutive' },
  { value: 'not_applicable', label: 'Not applicable' },
];

const VERB_ASPECT_OPTIONS = [
  { value: 'perfective', label: 'Perfective' },
  { value: 'imperfective', label: 'Imperfective' },
  { value: 'progressive', label: 'Progressive' },
  { value: 'continuous', label: 'Continuous' },
  { value: 'habitual', label: 'Habitual' },
  { value: 'iterative', label: 'Iterative' },
  { value: 'inchoative', label: 'Inchoative' },
  { value: 'perfect', label: 'Perfect' },
  { value: 'prospective', label: 'Prospective' },
  { value: 'not_applicable', label: 'Not applicable' },
  { value: 'other', label: 'Other' },
];

const ANIMACY_OPTIONS = [
  { value: 'animate', label: 'Animate' },
  { value: 'inanimate', label: 'Inanimate' },
  { value: 'human', label: 'Human' },
  { value: 'non_human', label: 'Non-human' },
  { value: 'personal', label: 'Personal' },
  { value: 'impersonal', label: 'Impersonal' },
  { value: 'not_applicable', label: 'Not applicable' },
];

const REGISTER_OPTIONS = [
  { value: 'formal', label: 'Formal' },
  { value: 'informal', label: 'Informal' },
  { value: 'colloquial', label: 'Colloquial' },
  { value: 'slang', label: 'Slang' },
  { value: 'ceremonial', label: 'Ceremonial' },
  { value: 'archaic', label: 'Archaic' },
  { value: 'taboo', label: 'Taboo' },
  { value: 'poetic', label: 'Poetic' },
  { value: 'technical', label: 'Technical' },
  { value: 'neutral', label: 'Neutral' },
];

const parseTags = (value: string): string[] =>
  value
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);

const isLetter = (char: string | undefined): boolean => {
  if (!char) return false;
  return LETTER_REGEX.test(char);
};

const expandRangeToWholeWords = (content: string, start: number, end: number) => {
  const length = content.length;
  if (length === 0) return null;

  let rangeStart = Math.max(0, Math.min(start, length));
  let rangeEnd = Math.max(0, Math.min(end, length));

  if (rangeStart > rangeEnd) {
    const temp = rangeStart;
    rangeStart = rangeEnd;
    rangeEnd = temp;
  }

  while (rangeStart < rangeEnd && !isLetter(content[rangeStart])) {
    rangeStart += 1;
  }

  while (rangeEnd > rangeStart && !isLetter(content[rangeEnd - 1])) {
    rangeEnd -= 1;
  }

  if (rangeStart >= rangeEnd) {
    return null;
  }

  while (rangeStart > 0 && isLetter(content[rangeStart - 1])) {
    rangeStart -= 1;
  }

  while (rangeEnd < length && isLetter(content[rangeEnd])) {
    rangeEnd += 1;
  }

  return { start: rangeStart, end: rangeEnd };
};

const expandCaretToWord = (content: string, offset: number) => {
  const length = content.length;
  if (length === 0) return null;

  let start = Math.max(0, Math.min(offset, length));
  let end = start;

  const hasLeft = start > 0 && isLetter(content[start - 1]);
  const hasRight = end < length && isLetter(content[end]);

  if (!hasLeft && !hasRight) {
    return null;
  }

  while (start > 0 && isLetter(content[start - 1])) {
    start -= 1;
  }

  while (end < length && isLetter(content[end])) {
    end += 1;
  }

  if (start === end) {
    return null;
  }

  return { start, end };
};

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

/**
 * Search result enriched with the data the user actually needs to
 * confirm "yes, this is the right word":
 * - IPA + romanization from the lemma form
 * - POS, gender, register from the lexeme itself
 * - notes (often a sense disambiguator like "3sg present indicative of sei")
 * - translations into other languages (key signal for cross-language IDs)
 */
interface EnrichedSearchHit extends LexemeWithForms {
  translations: TranslationLink[];
}

/**
 * Build a tooltip describing the dictionary entry a link points at. Used for
 * both the Suggestions list and the Selection panel. The visible row only
 * shows the form (e.g. "is"); the tooltip carries the disambiguating
 * metadata — most importantly the parent lemma when the form is an
 * inflection (e.g. "is" → lemma "sei").
 *
 * Shape:
 *   <form>
 *   Form of "<lemma>" — <first-line of lemma notes>          (only if form ≠ lemma)
 *   <word_form_notes>                                         (e.g. "3sg present indicative")
 *   /<romanization>/ · /<IPA>/                               (only if present)
 *   <lemma notes>                                             (full notes block)
 */
function buildLinkTooltip(link: TextWordLink): string {
  const form = link.word_text ?? '';
  const lemma = link.word_lemma;
  const isInflection = !!(lemma && form && lemma !== form);
  const lemmaMeaningSnippet = link.word_notes?.split(/[.\n]/)[0]?.trim();
  const pronunciation = [
    link.word_form_romanization ? `/${link.word_form_romanization}/` : '',
    link.word_form_ipa ? `[${link.word_form_ipa}]` : '',
  ]
    .filter(Boolean)
    .join(' · ');
  return [
    form,
    isInflection
      ? `Form of "${lemma}"${lemmaMeaningSnippet ? ` — ${lemmaMeaningSnippet}` : ''}`
      : '',
    link.word_form_notes ?? '',
    pronunciation,
    // Avoid duplicating the lemma meaning snippet we already showed above.
    link.word_notes && link.word_notes !== lemmaMeaningSnippet
      ? link.word_notes
      : !isInflection && link.word_notes
        ? link.word_notes
        : '',
  ]
    .filter(Boolean)
    .join('\n');
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
  const [autoExpandSelection, setAutoExpandSelection] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  // Tracks which suggestion the user is currently hovering, so the matching
  // span in the document body can be visually highlighted. {start, end} is
  // a char range within the active text.
  const [hoveredSpan, setHoveredSpan] = useState<{ start: number; end: number } | null>(null);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const [searchResults, setSearchResults] = useState<EnrichedSearchHit[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const [showNewWordForm, setShowNewWordForm] = useState(false);
  const [newWordData, setNewWordData] = useState<{
    lemma: string;
    romanization?: string;
    ipa_pronunciation?: string;
    part_of_speech?: string;
    gender?: string;
    plurality?: string;
    grammatical_case?: string;
    verb_aspect?: string;
    animacy?: string;
    language_register?: string;
    definition?: string;
    literal_translation?: string;
    context_notes?: string;
    usage_examples?: string;
  }>({
    lemma: '',
    language_register: 'neutral',
  });
  const [newWordTagsInput, setNewWordTagsInput] = useState('');

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

  useEffect(() => {
    const selectedWord = selectedSpan?.text?.trim() ?? '';
    setNewWordData((prev) => ({
      ...prev,
      word: selectedWord,
    }));
  }, [selectedSpan?.text]);

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
    // Unicode-aware: \p{L}+\p{M} covers letters with diacritics like "ó",
    // \p{N} keeps digit-bearing tokens, and we allow apostrophe + hyphen
    // for contractions like "gibd's". The previous /[\w'-]+/ only matched
    // ASCII so it sliced "sógn" into "s"/"gn" and similar.
    const tokenRegex = /[\p{L}\p{M}\p{N}'-]+/gu;
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

      const element: HTMLElement | null =
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

  const applySelectionRange = useCallback(
    (start: number, end: number) => {
      if (!activeText) return;
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
    },
    [activeText],
  );

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

  const updateSelectionFromNative = useCallback(() => {
    const container = textContainerRef.current;
    if (!container || !activeText) return;

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
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

    const rawStart = Math.min(startOffset, endOffset);
    const rawEnd = Math.max(startOffset, endOffset);

    if (!autoExpandSelection) {
      applySelectionRange(rawStart, rawEnd);
      return;
    }

    if (rawStart === rawEnd) {
      setSelectedSpan(null);
      return;
    }

    const expanded = expandRangeToWholeWords(activeText.content, rawStart, rawEnd);
    if (!expanded) {
      setSelectedSpan(null);
      return;
    }

    const { start, end } = expanded;
    selectRangeInText(start, end);
    applySelectionRange(start, end);
  }, [activeText, applySelectionRange, getOffsetFromNode, selectRangeInText, autoExpandSelection]);

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

  const handleLinkToWord = async (lexemeId: string) => {
    if (!activeText || !selectedSpan) return;
    setIsSaving(true);
    setActionError(null);
    try {
      // Search results are Lexemes; the link points at a WordForm. Resolve
      // the lexeme's lemma form on the fly.
      const lexeme = await wordService.getById(lexemeId);
      const lemmaForm = lexeme.forms.find((f) => f.is_lemma) ?? lexeme.forms[0];
      if (!lemmaForm) {
        setActionError('Lexeme has no forms to link');
        return;
      }
      const payload: TextWordLinkCreate = {
        word_form_id: lemmaForm.id,
        start_char: selectedSpan.start,
        end_char: selectedSpan.end,
        status: TextWordLinkStatus.CONFIRMED,
      };
      const link = await wordLinkService.create(activeText.id, payload);
      applyLinkUpdate(link);
      setActionMessage('Link created successfully.');
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
    if (!selectedLanguage?.id) {
      setSearchResults([]);
      return;
    }

    const query = selectedSpan?.text?.trim();
    if (!query) {
      setActionError('Select some text in the document to search for similar words.');
      return;
    }

    setActionError(null);
    setActionMessage(null);
    setSearchLoading(true);
    try {
      const results = await wordService.search({
        q: query.slice(0, 100),
        language_ids: selectedLanguage.id,
        include_unpublished: true,
        limit: 10,
      });
      // Fetch each result's translations in parallel so the user sees
      // the cross-language meaning right next to the lemma. Errors per
      // result fall back to an empty translations list.
      const enriched: EnrichedSearchHit[] = await Promise.all(
        results.map(async (r) => {
          try {
            const translations = await wordService.listTranslations(r.id);
            return { ...r, translations };
          } catch {
            return { ...r, translations: [] };
          }
        }),
      );
      setSearchResults(enriched);
      if (enriched.length === 0) {
        setActionMessage('No similar words found for the current selection.');
      }
    } catch (err) {
      setSearchResults([]);
      setActionError('Failed to search for similar words.');
    } finally {
      setSearchLoading(false);
    }
  }, [selectedLanguage?.id, selectedSpan?.text]);

  const clearSelection = useCallback(() => {
    setSelectedSpan(null);
    const selection = window.getSelection();
    selection?.removeAllRanges();
  }, []);

  const handleTextMouseUp = useCallback(() => {
    const container = textContainerRef.current;
    if (!container || !activeText) return;

    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      setSelectedSpan(null);
      return;
    }

    const range = selection.getRangeAt(0);
    if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) {
      setSelectedSpan(null);
      return;
    }

    if (selection.isCollapsed) {
      const caretOffset = getOffsetFromNode(range.startContainer, range.startOffset);
      if (caretOffset === null) {
        setSelectedSpan(null);
        selection.removeAllRanges();
        return;
      }

      if (!autoExpandSelection) {
        setSelectedSpan(null);
        selection.removeAllRanges();
        return;
      }

      const expanded = expandCaretToWord(activeText.content, caretOffset);
      if (!expanded) {
        setSelectedSpan(null);
        selection.removeAllRanges();
        return;
      }

      const { start, end } = expanded;
      selectRangeInText(start, end);
      applySelectionRange(start, end);
    } else {
      updateSelectionFromNative();
    }
  }, [
    activeText,
    applySelectionRange,
    getOffsetFromNode,
    selectRangeInText,
    updateSelectionFromNative,
    autoExpandSelection,
  ]);
  const handleCreateWordAndLink = async () => {
    if (!activeText || !selectedSpan) return;
    const trimmedLemma = (newWordData.lemma ?? '').trim();
    if (!trimmedLemma) {
      setActionError('Word is required before creating a new entry.');
      return;
    }
    setIsSaving(true);
    setActionError(null);
    try {
      const targetLanguageId = activeText.language_id ?? selectedLanguage.id;
      const tags = parseTags(newWordTagsInput);
      const trim = (v?: string) => v?.trim() || undefined;

      const payload: CreateLexemeData = {
        language_id: targetLanguageId,
        lemma: trimmedLemma,
        lemma_form: {
          form: trimmedLemma,
          is_lemma: true,
          romanization: trim(newWordData.romanization),
          ipa_pronunciation: trim(newWordData.ipa_pronunciation),
          plurality: newWordData.plurality || undefined,
          grammatical_case: newWordData.grammatical_case || undefined,
          verb_aspect: newWordData.verb_aspect || undefined,
        },
        part_of_speech: newWordData.part_of_speech || undefined,
        gender: newWordData.gender || undefined,
        animacy: newWordData.animacy || undefined,
        language_register: newWordData.language_register || undefined,
        tags: tags.length > 0 ? tags : undefined,
      };

      const newWord = await wordService.create(payload);
      // newWord is a LexemeWithForms; pick the lemma form for the link.
      const lemmaForm = newWord.forms.find((f) => f.is_lemma) ?? newWord.forms[0];
      if (!lemmaForm) {
        setActionError('Created lexeme has no form to link to');
        return;
      }
      const linkPayload: TextWordLinkCreate = {
        word_form_id: lemmaForm.id,
        start_char: selectedSpan.start,
        end_char: selectedSpan.end,
        status: TextWordLinkStatus.CONFIRMED,
      };
      const link = await wordLinkService.create(activeText.id, linkPayload);
      applyLinkUpdate(link);

      setNewWordData({
        lemma: '',
        language_register: 'neutral',
      });
      setNewWordTagsInput('');
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
          <button
            className="btn-link"
            onClick={handleBackToDocument}
            title="Return to the document detail page"
          >
            ← Back to Document
          </button>
          <h1>Link Words · {activeText.title}</h1>
          <p className="document-linking-subtitle">
            {activeLanguageDisplay} · {getDocumentTypeLabel(activeText.document_type)}
          </p>
        </div>
        <div className="document-linking-actions">
          <label
            className="toggle-control"
            title="When on, clicking a single word inside a longer phrase will expand the selection to the whole word boundary."
          >
            <input
              type="checkbox"
              checked={autoExpandSelection}
              onChange={(event) => setAutoExpandSelection(event.target.checked)}
            />
            <span>Auto-expand selection</span>
          </label>
          <button
            className="btn-secondary"
            onClick={handleRegenerateSuggestionsForText}
            disabled={!canEdit || isSuggesting}
            title="Rebuild auto-suggested word links for THIS text only. Existing confirmed or rejected links are preserved; new suggestions appear where matching dictionary words are found."
          >
            {isSuggesting ? 'Rebuilding…' : 'Regenerate Text Suggestions'}
          </button>
          <button
            className="btn-secondary"
            onClick={handleRegenerateForDocument}
            disabled={!canEdit || isSuggesting}
            title="Rebuild auto-suggested word links for EVERY text in this document (all translations). Existing confirmed or rejected links are preserved."
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
            onMouseUp={handleTextMouseUp}
          >
            {tokens.map((token) => (
              <span
                key={token.id}
                data-start={token.start}
                data-end={token.end}
                className={[
                  'linking-token',
                  token.type === 'whitespace' ? 'token-whitespace' : 'token-word',
                  // Only colour-code linkable word tokens; whitespace and
                  // punctuation runs render as plain text rather than
                  // looking like an unlinked-yellow target.
                  token.type === 'word' ? `status-${token.status}` : '',
                  selectedSpan &&
                  token.start >= selectedSpan.start &&
                  token.end <= selectedSpan.end
                    ? 'selected'
                    : '',
                  hoveredSpan &&
                  token.start >= hoveredSpan.start &&
                  token.end <= hoveredSpan.end
                    ? 'suggestion-hover'
                    : '',
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
                <div className="selection-toolbar">
                  <button
                    type="button"
                    className="btn-link"
                    onClick={clearSelection}
                    title="Deselect the current span without changing any links"
                  >
                    Clear selection
                  </button>
                </div>
                {selectedSpan.link ? (
                  <div className="selection-actions">
                    <div
                      className="selection-meta"
                      title={buildLinkTooltip(selectedSpan.link)}
                    >
                      <strong>Word:</strong>{' '}
                      <span className="selection-meta-word">
                        {selectedSpan.link.word_text ??
                          `#${selectedSpan.link.word_form_id}`}
                      </span>
                      {selectedSpan.link.word_part_of_speech && (
                        <span className="selection-meta-pos">
                          {selectedSpan.link.word_part_of_speech}
                        </span>
                      )}
                    </div>
                    <div className="selection-buttons">
                      <button
                        className="btn-primary"
                        onClick={() => handleConfirmLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                        title="Accept this suggested link — the span will be marked as a confirmed dictionary reference."
                      >
                        Confirm
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRejectLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                        title="Mark this suggestion as wrong. It stays in the database (so it's not re-suggested) but no longer counts as a link."
                      >
                        Reject
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRemoveLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                        title="Delete this link entirely. The span becomes unlinked, and the next Regenerate may suggest it again."
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
                        title="Find dictionary entries that start with the selected text. Results show meanings; hover any for full detail."
                      >
                        {searchLoading ? 'Searching…' : 'Search existing words'}
                      </button>
                    </div>
                    <div className="search-results">
                      {searchLoading && <p>Searching…</p>}
                      {!searchLoading && searchResults.length === 0 && (
                        <p>No words found.</p>
                      )}
                      {searchResults.map((word) => {
                        const lemmaForm =
                          word.forms?.find((f) => f.is_lemma) ?? word.forms?.[0];
                        const metaBits = [
                          word.part_of_speech,
                          word.gender,
                          word.animacy,
                        ].filter(Boolean) as string[];
                        const translationsText = word.translations
                          .map((t) => t.lemma)
                          .join(', ');
                        const tooltip = [
                          word.lemma,
                          metaBits.length > 0 ? `[${metaBits.join(' · ')}]` : '',
                          lemmaForm?.romanization
                            ? `Romanization: ${lemmaForm.romanization}`
                            : '',
                          lemmaForm?.ipa_pronunciation
                            ? `IPA: /${lemmaForm.ipa_pronunciation}/`
                            : '',
                          translationsText ? `Translations: ${translationsText}` : '',
                          word.notes ? `Notes: ${word.notes}` : '',
                        ]
                          .filter(Boolean)
                          .join('\n');
                        return (
                          <div
                            key={word.id}
                            className="search-result"
                            title={tooltip}
                          >
                            <div className="search-result-body">
                              <div className="search-result-headline">
                                <strong>{word.lemma}</strong>
                                {lemmaForm?.romanization && (
                                  <span className="search-result-roman">
                                    /{lemmaForm.romanization}/
                                  </span>
                                )}
                                {word.part_of_speech && (
                                  <span className="search-result-pos">
                                    {word.part_of_speech}
                                  </span>
                                )}
                              </div>
                              {translationsText && (
                                <div className="search-definition">
                                  {translationsText}
                                </div>
                              )}
                              {word.notes && (
                                <div className="search-result-notes">{word.notes}</div>
                              )}
                            </div>
                            <button
                              className="btn-primary"
                              onClick={() => handleLinkToWord(word.id)}
                              disabled={!canEdit || isSaving}
                              title={`Link the selected text to "${word.lemma}"${
                                translationsText ? ` (${translationsText})` : ''
                              }`}
                            >
                              Link
                            </button>
                          </div>
                        );
                      })}
                    </div>
                    <div className="new-word-section">
                      {!showNewWordForm ? (
                        <button
                          className="btn-secondary"
                          onClick={() => {
                            const targetLanguageId =
                              activeText?.language_id ?? selectedLanguage.id;
                            void targetLanguageId;
                            setNewWordData({
                              lemma: selectedSpan?.text?.trim() ?? '',
                              romanization: '',
                              ipa_pronunciation: '',
                              part_of_speech: '',
                              gender: '',
                              plurality: '',
                              grammatical_case: '',
                              verb_aspect: '',
                              animacy: '',
                              language_register: 'neutral',
                              definition: '',
                              literal_translation: '',
                              context_notes: '',
                              usage_examples: '',
                            });
                            setNewWordTagsInput('');
                            setShowNewWordForm(true);
                          }}
                          disabled={!canEdit}
                          title="Open a form to add this span as a brand-new dictionary entry, then link the selection to it in one step."
                        >
                          Create new word
                        </button>
                      ) : (
                        <div className="new-word-form">
                          <label htmlFor="new-word">Word *</label>
                          <input
                            id="new-word"
                            type="text"
                            value={newWordData.lemma}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, lemma: event.target.value }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-romanization">Romanization</label>
                          <input
                            id="new-word-romanization"
                            type="text"
                            value={newWordData.romanization || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                romanization: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-ipa">IPA Pronunciation</label>
                          <input
                            id="new-word-ipa"
                            type="text"
                            value={newWordData.ipa_pronunciation || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                ipa_pronunciation: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-part-of-speech">Part of Speech</label>
                          <select
                            id="new-word-part-of-speech"
                            value={newWordData.part_of_speech || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                part_of_speech: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {PART_OF_SPEECH_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-gender">Gender</label>
                          <select
                            id="new-word-gender"
                            value={newWordData.gender || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                gender: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {GENDER_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-plurality">Plurality</label>
                          <select
                            id="new-word-plurality"
                            value={newWordData.plurality || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                plurality: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {PLURALITY_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-case">Grammatical Case</label>
                          <select
                            id="new-word-case"
                            value={newWordData.grammatical_case || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                grammatical_case: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {CASE_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-verb-aspect">Verb Aspect</label>
                          <select
                            id="new-word-verb-aspect"
                            value={newWordData.verb_aspect || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                verb_aspect: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {VERB_ASPECT_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-animacy">Animacy</label>
                          <select
                            id="new-word-animacy"
                            value={newWordData.animacy || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                animacy: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {ANIMACY_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-register">Language Register</label>
                          <select
                            id="new-word-register"
                            value={newWordData.language_register || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                language_register: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          >
                            <option value="">Select...</option>
                            {REGISTER_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-definition">Definition</label>
                          <textarea
                            id="new-word-definition"
                            rows={3}
                            value={newWordData.definition || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, definition: event.target.value }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-literal">Literal Translation</label>
                          <textarea
                            id="new-word-literal"
                            rows={2}
                            value={newWordData.literal_translation || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                literal_translation: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-context">Context Notes</label>
                          <textarea
                            id="new-word-context"
                            rows={2}
                            value={newWordData.context_notes || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                context_notes: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-usage">Usage Examples</label>
                          <textarea
                            id="new-word-usage"
                            rows={3}
                            value={newWordData.usage_examples || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({
                                ...prev,
                                usage_examples: event.target.value,
                              }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-tags">Tags (comma separated)</label>
                          <input
                            id="new-word-tags"
                            type="text"
                            value={newWordTagsInput}
                            onChange={(event) => setNewWordTagsInput(event.target.value)}
                            disabled={!canEdit}
                            placeholder="e.g., nature, ceremonial"
                          />

                          <div className="new-word-actions">
                            <button
                              className="btn-primary"
                              onClick={handleCreateWordAndLink}
                              disabled={
                                !canEdit ||
                                isSaving ||
                                !newWordData.lemma.trim()
                              }
                              title="Save this as a new dictionary entry and immediately link the selected text to it."
                            >
                              Create & Link
                            </button>
                            <button
                              className="btn-secondary"
                              onClick={() => {
                                setShowNewWordForm(false);
                                setNewWordTagsInput('');
                                setNewWordData({
                                  lemma: selectedSpan?.text?.trim() ?? '',
                                  romanization: '',
                                  ipa_pronunciation: '',
                                  part_of_speech: '',
                                  gender: '',
                                  plurality: '',
                                  grammatical_case: '',
                                  verb_aspect: '',
                                  animacy: '',
                                  language_register: 'neutral',
                                  definition: '',
                                  literal_translation: '',
                                  context_notes: '',
                                  usage_examples: '',
                                });
                              }}
                              disabled={isSaving}
                              title="Close the form and discard the new-word details"
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
                {suggestions.map((link) => {
                  // The row shows ONE word — the form being linked, which is
                  // also the text in the document (they are the same string
                  // by construction). Lemma + inflection role live in the
                  // hover tooltip; the row stays scannable.
                  const formLabel =
                    link.word_text ??
                    activeText.content.slice(link.start_char, link.end_char);
                  const linkTooltip = buildLinkTooltip(link);
                  return (
                    <li
                      key={link.id}
                      className="suggestion-item"
                      // Hovering anywhere on the row highlights the matching
                      // span in the document body. Clears on mouse-leave.
                      onMouseEnter={() =>
                        setHoveredSpan({ start: link.start_char, end: link.end_char })
                      }
                      onMouseLeave={() => setHoveredSpan(null)}
                      title={linkTooltip}
                    >
                      <div className="suggestion-headline">
                        <span className="suggestion-form">{formLabel}</span>
                        {link.word_part_of_speech && (
                          <span className="suggestion-pos">
                            {link.word_part_of_speech}
                          </span>
                        )}
                      </div>
                      <div className="suggestion-actions">
                        <button
                          className="btn-primary"
                          onClick={() => handleConfirmLink(link)}
                          disabled={!canEdit || isSaving}
                          title="Accept this suggestion as a confirmed link without leaving the suggestions list."
                        >
                          Confirm
                        </button>
                        <button
                          className="btn-secondary"
                          onClick={() => handleRejectLink(link)}
                          disabled={!canEdit || isSaving}
                          title="Mark this suggestion as wrong. It won't be re-proposed by future Regenerate runs."
                        >
                          Reject
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
