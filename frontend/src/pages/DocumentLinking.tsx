import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

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
import { languageDisplayName } from '../utils/languageName';
import './DocumentLinking.css';

// Mirror backend app.utils.text_normalize.fold_for_match so the UI can tell
// when a selected span is genuinely a different spelling from the form it's
// being linked to — and not just a case/accent variant the backend rejects.
function foldToken(value: string): string {
  return (value || '')
    .normalize('NFD')
    .replace(/\p{Mn}/gu, '')
    .toLowerCase();
}

// A dictionary entry the typed new-word already matches — either as an exact
// standard form, or via a recorded non-standard spelling.
interface DuplicateHint {
  lexemeId: string;
  standardForm: string;
  viaVariant: boolean;
}

const LETTER_REGEX =
  (() => {
    try {
      return new RegExp('\\p{L}', 'u');
    } catch {
      return /[A-Za-z]/;
    }
  })();

// `label` values are i18n keys, resolved with t() at render time.
const PART_OF_SPEECH_OPTIONS = [
  { value: 'noun', label: 'linking.opt_noun' },
  { value: 'verb', label: 'linking.opt_verb' },
  { value: 'adjective', label: 'linking.opt_adjective' },
  { value: 'adverb', label: 'linking.opt_adverb' },
  { value: 'pronoun', label: 'linking.opt_pronoun' },
  { value: 'preposition', label: 'linking.opt_preposition' },
  { value: 'conjunction', label: 'linking.opt_conjunction' },
  { value: 'interjection', label: 'linking.opt_interjection' },
  { value: 'article', label: 'linking.opt_article' },
  { value: 'determiner', label: 'linking.opt_determiner' },
  { value: 'particle', label: 'linking.opt_particle' },
  { value: 'numeral', label: 'linking.opt_numeral' },
  { value: 'classifier', label: 'linking.opt_classifier' },
  { value: 'other', label: 'linking.opt_other' },
];

const GENDER_OPTIONS = [
  { value: 'masculine', label: 'linking.opt_masculine' },
  { value: 'feminine', label: 'linking.opt_feminine' },
  { value: 'neuter', label: 'linking.opt_neuter' },
  { value: 'common', label: 'linking.opt_common' },
  { value: 'animate', label: 'linking.opt_animate' },
  { value: 'inanimate', label: 'linking.opt_inanimate' },
  { value: 'not_applicable', label: 'linking.opt_not_applicable' },
];

const PLURALITY_OPTIONS = [
  { value: 'singular', label: 'linking.opt_singular' },
  { value: 'plural', label: 'linking.opt_plural' },
  { value: 'dual', label: 'linking.opt_dual' },
  { value: 'trial', label: 'linking.opt_trial' },
  { value: 'paucal', label: 'linking.opt_paucal' },
  { value: 'collective', label: 'linking.opt_collective' },
  { value: 'not_applicable', label: 'linking.opt_not_applicable' },
];

const CASE_OPTIONS = [
  { value: 'nominative', label: 'linking.opt_nominative' },
  { value: 'accusative', label: 'linking.opt_accusative' },
  { value: 'genitive', label: 'linking.opt_genitive' },
  { value: 'dative', label: 'linking.opt_dative' },
  { value: 'ablative', label: 'linking.opt_ablative' },
  { value: 'locative', label: 'linking.opt_locative' },
  { value: 'instrumental', label: 'linking.opt_instrumental' },
  { value: 'vocative', label: 'linking.opt_vocative' },
  { value: 'partitive', label: 'linking.opt_partitive' },
  { value: 'comitative', label: 'linking.opt_comitative' },
  { value: 'essive', label: 'linking.opt_essive' },
  { value: 'translative', label: 'linking.opt_translative' },
  { value: 'ergative', label: 'linking.opt_ergative' },
  { value: 'absolutive', label: 'linking.opt_absolutive' },
  { value: 'not_applicable', label: 'linking.opt_not_applicable' },
];

const VERB_ASPECT_OPTIONS = [
  { value: 'perfective', label: 'linking.opt_perfective' },
  { value: 'imperfective', label: 'linking.opt_imperfective' },
  { value: 'progressive', label: 'linking.opt_progressive' },
  { value: 'continuous', label: 'linking.opt_continuous' },
  { value: 'habitual', label: 'linking.opt_habitual' },
  { value: 'iterative', label: 'linking.opt_iterative' },
  { value: 'inchoative', label: 'linking.opt_inchoative' },
  { value: 'perfect', label: 'linking.opt_perfect' },
  { value: 'prospective', label: 'linking.opt_prospective' },
  { value: 'not_applicable', label: 'linking.opt_not_applicable' },
  { value: 'other', label: 'linking.opt_other' },
];

const ANIMACY_OPTIONS = [
  { value: 'animate', label: 'linking.opt_animate' },
  { value: 'inanimate', label: 'linking.opt_inanimate' },
  { value: 'human', label: 'linking.opt_human' },
  { value: 'non_human', label: 'linking.opt_non_human' },
  { value: 'personal', label: 'linking.opt_personal' },
  { value: 'impersonal', label: 'linking.opt_impersonal' },
  { value: 'not_applicable', label: 'linking.opt_not_applicable' },
];

const REGISTER_OPTIONS = [
  { value: 'formal', label: 'linking.opt_formal' },
  { value: 'informal', label: 'linking.opt_informal' },
  { value: 'colloquial', label: 'linking.opt_colloquial' },
  { value: 'slang', label: 'linking.opt_slang' },
  { value: 'ceremonial', label: 'linking.opt_ceremonial' },
  { value: 'archaic', label: 'linking.opt_archaic' },
  { value: 'taboo', label: 'linking.opt_taboo' },
  { value: 'poetic', label: 'linking.opt_poetic' },
  { value: 'technical', label: 'linking.opt_technical' },
  { value: 'neutral', label: 'linking.opt_neutral' },
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
function buildLinkTooltip(
  link: TextWordLink,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
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
      ? `${t('linking.form_of', { lemma })}${lemmaMeaningSnippet ? ` — ${lemmaMeaningSnippet}` : ''}`
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
  const { t } = useTranslation();
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

  // When linking a span whose spelling differs from the target form, also
  // record the original span as an alternative spelling. On by default — this
  // is the main way the spelling map gets populated during linking.
  const [recordAltSpelling, setRecordAltSpelling] = useState(true);
  // Existing entries the typed new-word already matches (exact form or variant).
  const [duplicateHints, setDuplicateHints] = useState<DuplicateHint[]>([]);

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
        setError(err?.response?.data?.detail || t('linking.failed_load_document'));
      } finally {
        if (withLoader) {
          setLoading(false);
        }
      }
    },
    [documentId, activeTextId, initialState, selectedLanguage.id, t],
  );

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  // Toast auto-dismiss timers. Success messages dismiss faster; errors
  // linger so the user has time to read them.
  useEffect(() => {
    if (!actionMessage) return;
    const timer = setTimeout(() => setActionMessage(null), 4000);
    return () => clearTimeout(timer);
  }, [actionMessage]);

  useEffect(() => {
    if (!actionError) return;
    const timer = setTimeout(() => setActionError(null), 8000);
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

  // Suggestions that were a unique exact dictionary match (the linker
  // auto-confirms these on new texts; older texts may still carry them).
  const exactSuggestionCount = useMemo(
    () => suggestions.filter((link) => (link.confidence ?? 0) >= 1).length,
    [suggestions],
  );

  // Live coverage over the page's own token model, so the numbers move as
  // links are confirmed without a server round-trip. Matches the learning
  // path's gate (90% of word tokens confirmed).
  const coverageStats = useMemo(() => {
    const wordTokens = tokens.filter((token) => token.type === 'word');
    const confirmed = wordTokens.filter(
      (token) => token.status === TextWordLinkStatus.CONFIRMED,
    ).length;
    return {
      total: wordTokens.length,
      unlinked: wordTokens.length - confirmed,
      coverage: wordTokens.length ? confirmed / wordTokens.length : 0,
    };
  }, [tokens]);

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

  // If enabled and the span's spelling differs from the linked form, record the
  // original span as an alternative spelling of that form. Best-effort: the
  // link already succeeded, so a rejected/duplicate variant is non-fatal.
  const maybeRecordAltSpelling = async (wordFormId: string, formText: string) => {
    const original = selectedSpan?.text?.trim();
    if (!recordAltSpelling || !original) return false;
    if (foldToken(original) === foldToken(formText)) return false;
    try {
      await wordService.addSpelling(wordFormId, { variant: original });
      return true;
    } catch {
      return false;
    }
  };

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
        setActionError(t('linking.lexeme_no_forms'));
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
      const recorded = await maybeRecordAltSpelling(lemmaForm.id, lemmaForm.form);
      setActionMessage(
        recorded
          ? t('linking.linked_saved_alt_spelling', {
              original: selectedSpan.text?.trim(),
              form: lemmaForm.form,
            })
          : t('linking.link_created'),
      );
      setSearchResults([]);
      setDuplicateHints([]);
      setShowNewWordForm(false);
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_create_link'));
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
      setActionMessage(t('linking.link_confirmed'));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_confirm_link'));
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
      setActionMessage(t('linking.suggestion_rejected'));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_reject_suggestion'));
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
      setActionMessage(t('linking.link_removed'));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_remove_link'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmExact = async () => {
    if (!activeText) return;
    setIsSaving(true);
    setActionError(null);
    const count = exactSuggestionCount;
    try {
      const refreshed = await wordLinkService.confirmExact(activeText.id);
      setDocumentData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          texts: prev.texts.map((text) =>
            text.id === activeText.id ? { ...text, word_links: refreshed } : text,
          ),
        };
      });
      setActionMessage(t('linking.exact_confirmed', { count }));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_confirm_exact'));
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
      setActionMessage(t('linking.suggestions_regenerated_text'));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_regenerate_suggestions'));
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
      setActionMessage(t('linking.suggestions_regenerated_all'));
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_regenerate_doc_suggestions'));
    } finally {
      setIsSuggesting(false);
    }
  };

  const runWordSearch = useCallback(
    async (silent = false) => {
    if (!selectedLanguage?.id) {
      setSearchResults([]);
      return;
    }

    const query = selectedSpan?.text?.trim();
    if (!query) {
      if (!silent) {
        setActionError(t('linking.select_text_to_search'));
      }
      return;
    }

    if (!silent) {
      setActionError(null);
      setActionMessage(null);
    }
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
      if (enriched.length === 0 && !silent) {
        setActionMessage(t('linking.no_similar_words'));
      }
    } catch {
      setSearchResults([]);
      if (!silent) {
        setActionError(t('linking.failed_search_words'));
      }
    } finally {
      setSearchLoading(false);
    }
    },
    [selectedLanguage?.id, selectedSpan?.text, t],
  );

  // Auto-search existing words whenever a fresh, unlinked span is selected, so
  // the user sees matches (including via alternative spellings) without having
  // to click — "eich" can now surface the standard "aih".
  useEffect(() => {
    if (selectedSpan && !selectedSpan.link && canEdit) {
      void runWordSearch(true);
    } else {
      setSearchResults([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSpan?.start, selectedSpan?.end, canEdit]);

  // While adding a new word, warn if the typed lemma already exists — as an
  // exact standard form or as a recorded non-standard spelling — so the user
  // links to the existing entry instead of creating a duplicate.
  useEffect(() => {
    if (!showNewWordForm || !selectedLanguage?.id) {
      setDuplicateHints([]);
      return;
    }
    const lemma = newWordData.lemma.trim();
    if (!lemma) {
      setDuplicateHints([]);
      return;
    }
    const handle = window.setTimeout(async () => {
      try {
        const resolution = await wordService.resolveSpelling(selectedLanguage.id, lemma);
        if (resolution.candidates.length > 0) {
          setDuplicateHints(
            resolution.candidates.map((c) => ({
              lexemeId: c.lexeme_id,
              standardForm: c.standard_form,
              viaVariant: true,
            })),
          );
          return;
        }
        if (resolution.already_standard) {
          const results = await wordService.search({
            q: lemma,
            language_ids: selectedLanguage.id,
            include_unpublished: true,
            limit: 8,
          });
          const folded = foldToken(lemma);
          const hits: DuplicateHint[] = [];
          results.forEach((lx) => {
            const match = (lx.forms ?? []).find((f) => foldToken(f.form) === folded);
            if (match) {
              hits.push({ lexemeId: lx.id, standardForm: match.form, viaVariant: false });
            }
          });
          setDuplicateHints(hits);
          return;
        }
        setDuplicateHints([]);
      } catch {
        setDuplicateHints([]);
      }
    }, 300);
    return () => window.clearTimeout(handle);
  }, [newWordData.lemma, showNewWordForm, selectedLanguage?.id]);

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
      setActionError(t('linking.word_required'));
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
        setActionError(t('linking.created_lexeme_no_form'));
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
      const recorded = await maybeRecordAltSpelling(lemmaForm.id, lemmaForm.form);

      setNewWordData({
        lemma: '',
        language_register: 'neutral',
      });
      setNewWordTagsInput('');
      setShowNewWordForm(false);
      setDuplicateHints([]);
      setActionMessage(
        recorded
          ? t('linking.word_created_linked_alt', { original: selectedSpan.text?.trim() })
          : t('linking.word_created_linked'),
      );
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || t('linking.failed_create_link_word'));
    } finally {
      setIsSaving(false);
    }
  };

  const formatLanguageDisplay = (text: Text | undefined) => {
    if (!text?.language_id) return t('linking.unknown_language');
    const language = languageMap.get(text.language_id.toString());
    if (!language) return t('linking.unknown_language');
    return `${languageDisplayName(language)}${
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
          <p>{t('linking.loading_document')}</p>
        </div>
      </div>
    );
  }

  if (error || !documentData || !activeText) {
    return (
      <div className="document-linking-page">
        <div className="error-state">
          <p>{error || t('linking.document_not_available')}</p>
          <button className="btn-secondary" onClick={handleBackToDocument}>
            {t('linking.back_to_document')}
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
            title={t('linking.back_to_document_title')}
          >
            ← {t('linking.back_to_document')}
          </button>
          <h1>{t('linking.link_words')} · {activeText.title}</h1>
          <p className="document-linking-subtitle">
            {activeLanguageDisplay} · {getDocumentTypeLabel(activeText.document_type)}
          </p>
          <p
            className={`document-linking-coverage ${
              coverageStats.coverage >= 0.9 ? 'coverage-ready' : ''
            }`}
          >
            {t('linking.coverage_line', {
              percent: Math.floor(coverageStats.coverage * 100),
              unlinked: coverageStats.unlinked,
            })}
            {coverageStats.coverage >= 0.9 && <> · ✓ {t('linking.coverage_ready')}</>}
          </p>
        </div>
        <div className="document-linking-actions">
          <button
            className="btn-primary"
            onClick={handleConfirmExact}
            disabled={!canEdit || isSaving || exactSuggestionCount === 0}
            title={t('linking.confirm_exact_title')}
          >
            {t('linking.confirm_exact', { count: exactSuggestionCount })}
          </button>
          <label
            className="toggle-control"
            title={t('linking.auto_expand_title')}
          >
            <input
              type="checkbox"
              checked={autoExpandSelection}
              onChange={(event) => setAutoExpandSelection(event.target.checked)}
            />
            <span>{t('linking.auto_expand_selection')}</span>
          </label>
          <button
            className="btn-secondary"
            onClick={handleRegenerateSuggestionsForText}
            disabled={!canEdit || isSuggesting}
            title={t('linking.regen_text_title')}
          >
            {isSuggesting ? t('linking.rebuilding') : t('linking.regen_text_suggestions')}
          </button>
          <button
            className="btn-secondary"
            onClick={handleRegenerateForDocument}
            disabled={!canEdit || isSuggesting}
            title={t('linking.regen_doc_title')}
          >
            {isSuggesting ? t('linking.working') : t('linking.regen_doc_suggestions')}
          </button>
        </div>
      </div>

      {!canEdit && (
        <div className="document-linking-info">
          {t('linking.read_only_info')}
        </div>
      )}

      {/* Toasts float in the bottom-right corner so they don't shift the
          page layout when they appear. Click × to dismiss; auto-dismiss
          after a few seconds (longer for errors so they're readable). */}
      {(actionError || actionMessage) && (
        <div className="document-linking-toasts" role="status" aria-live="polite">
          {actionError && (
            <div className="document-linking-toast toast-error">
              <span className="toast-body">{actionError}</span>
              <button
                type="button"
                className="toast-dismiss"
                onClick={() => setActionError(null)}
                aria-label={t('linking.dismiss_error')}
                title={t('linking.dismiss')}
              >
                ×
              </button>
            </div>
          )}
          {actionMessage && (
            <div className="document-linking-toast toast-success">
              <span className="toast-body">{actionMessage}</span>
              <button
                type="button"
                className="toast-dismiss"
                onClick={() => setActionMessage(null)}
                aria-label={t('linking.dismiss_message')}
                title={t('linking.dismiss')}
              >
                ×
              </button>
            </div>
          )}
        </div>
      )}

      <div className="document-linking-grid">
        <aside className="document-linking-sidebar">
          <h2>{t('linking.texts_heading')} ({documentData.texts.length})</h2>
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
                    {text.is_primary ? ` · ${t('linking.primary')}` : ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="document-linking-content">
          <div className="token-legend">
            <span className="legend-chip legend-unlinked">{t('linking.legend_unlinked')}</span>
            <span className="legend-chip legend-suggested">{t('linking.legend_suggested')}</span>
            <span className="legend-chip legend-confirmed">{t('linking.legend_linked')}</span>
            <span className="legend-chip legend-rejected">{t('linking.legend_rejected')}</span>
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
            <h2>{t('linking.selection_heading')}</h2>
            {selectedSpan ? (
              <>
                <div className="selection-preview">
                  <span className="selection-text">{selectedSpan.text}</span>
                  <span className={`selection-status status-${selectedStatus}`}>
                    {t(`linking.status_${selectedSpan.link ? selectedSpan.link.status : 'unlinked'}`)}
                  </span>
                </div>
                <div className="selection-toolbar">
                  <button
                    type="button"
                    className="btn-link"
                    onClick={clearSelection}
                    title={t('linking.clear_selection_title')}
                  >
                    {t('linking.clear_selection')}
                  </button>
                </div>
                {selectedSpan.link ? (
                  <div className="selection-actions">
                    <div
                      className="selection-meta"
                      title={buildLinkTooltip(selectedSpan.link, t)}
                    >
                      <strong>{t('linking.word_label')}</strong>{' '}
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
                        title={t('linking.confirm_link_title')}
                      >
                        {t('linking.confirm')}
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRejectLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                        title={t('linking.reject_link_title')}
                      >
                        {t('linking.reject')}
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleRemoveLink(selectedSpan.link!)}
                        disabled={!canEdit || isSaving}
                        title={t('linking.unlink_title')}
                      >
                        {t('linking.unlink')}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="selection-actions">
                    <p className="selection-help">
                      {t('linking.selection_help')}
                    </p>
                    {canEdit && (
                      <label
                        className="alt-spelling-toggle"
                        title={t('linking.alt_spelling_title')}
                      >
                        <input
                          type="checkbox"
                          checked={recordAltSpelling}
                          onChange={(event) => setRecordAltSpelling(event.target.checked)}
                        />
                        <span>
                          {t('linking.alt_spelling_label', { text: selectedSpan.text?.trim() })}
                        </span>
                      </label>
                    )}
                    <div className="link-existing">
                      <button
                        className="btn-secondary"
                        onClick={() => runWordSearch()}
                        disabled={!canEdit || searchLoading}
                        title={t('linking.search_words_title')}
                      >
                        {searchLoading ? t('linking.searching') : t('linking.search_existing_words')}
                      </button>
                    </div>
                    <div className="search-results">
                      {searchLoading && <p>{t('linking.searching')}</p>}
                      {!searchLoading && searchResults.length === 0 && (
                        <p>{t('linking.no_words_found')}</p>
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
                            ? t('linking.tooltip_romanization', { value: lemmaForm.romanization })
                            : '',
                          lemmaForm?.ipa_pronunciation
                            ? t('linking.tooltip_ipa', { value: lemmaForm.ipa_pronunciation })
                            : '',
                          translationsText
                            ? t('linking.tooltip_translations', { value: translationsText })
                            : '',
                          word.notes ? t('linking.tooltip_notes', { value: word.notes }) : '',
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
                              title={`${t('linking.link_to_word_title', { word: word.lemma })}${
                                translationsText ? ` (${translationsText})` : ''
                              }`}
                            >
                              {t('linking.link')}
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
                          title={t('linking.create_new_word_title')}
                        >
                          {t('linking.create_new_word')}
                        </button>
                      ) : (
                        <div className="new-word-form">
                          <label htmlFor="new-word">{t('linking.word_field')} *</label>
                          <input
                            id="new-word"
                            type="text"
                            value={newWordData.lemma}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, lemma: event.target.value }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-romanization">{t('linking.romanization')}</label>
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

                          <label htmlFor="new-word-ipa">{t('linking.ipa_pronunciation')}</label>
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

                          <label htmlFor="new-word-part-of-speech">{t('linking.part_of_speech')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {PART_OF_SPEECH_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-gender">{t('linking.gender')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {GENDER_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-plurality">{t('linking.plurality')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {PLURALITY_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-case">{t('linking.grammatical_case')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {CASE_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-verb-aspect">{t('linking.verb_aspect')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {VERB_ASPECT_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-animacy">{t('linking.animacy')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {ANIMACY_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-register">{t('linking.language_register')}</label>
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
                            <option value="">{t('linking.select_placeholder')}</option>
                            {REGISTER_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {t(option.label)}
                              </option>
                            ))}
                          </select>

                          <label htmlFor="new-word-definition">{t('linking.definition')}</label>
                          <textarea
                            id="new-word-definition"
                            rows={3}
                            value={newWordData.definition || ''}
                            onChange={(event) =>
                              setNewWordData((prev) => ({ ...prev, definition: event.target.value }))
                            }
                            disabled={!canEdit}
                          />

                          <label htmlFor="new-word-literal">{t('linking.literal_translation')}</label>
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

                          <label htmlFor="new-word-context">{t('linking.context_notes')}</label>
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

                          <label htmlFor="new-word-usage">{t('linking.usage_examples')}</label>
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

                          <label htmlFor="new-word-tags">{t('linking.tags_label')}</label>
                          <input
                            id="new-word-tags"
                            type="text"
                            value={newWordTagsInput}
                            onChange={(event) => setNewWordTagsInput(event.target.value)}
                            disabled={!canEdit}
                            placeholder={t('linking.tags_placeholder')}
                          />

                          {duplicateHints.length > 0 && (
                            <div className="duplicate-hint" role="status">
                              <p className="duplicate-hint-lead">
                                {t('linking.duplicate_hint_lead')}
                              </p>
                              <ul className="duplicate-hint-list">
                                {duplicateHints.map((hint) => (
                                  <li key={hint.lexemeId} className="duplicate-hint-row">
                                    <span>
                                      <strong>{hint.standardForm}</strong>
                                      {hint.viaVariant && (
                                        <em className="duplicate-hint-via">
                                          {' · '}
                                          {t('linking.known_spelling_of', {
                                            word: newWordData.lemma.trim(),
                                          })}
                                        </em>
                                      )}
                                    </span>
                                    <button
                                      type="button"
                                      className="btn-secondary"
                                      onClick={() => handleLinkToWord(hint.lexemeId)}
                                      disabled={!canEdit || isSaving}
                                      title={t('linking.link_existing_title', {
                                        word: hint.standardForm,
                                      })}
                                    >
                                      {t('linking.link_to_this')}
                                    </button>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          <div className="new-word-actions">
                            <button
                              className="btn-primary"
                              onClick={handleCreateWordAndLink}
                              disabled={
                                !canEdit ||
                                isSaving ||
                                !newWordData.lemma.trim()
                              }
                              title={t('linking.create_and_link_title')}
                            >
                              {t('linking.create_and_link')}
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
                              title={t('linking.cancel_new_word_title')}
                            >
                              {t('linking.cancel')}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p>{t('linking.highlight_help')}</p>
            )}
          </section>

          <section className="suggestions-section">
            <h2>{t('linking.suggestions_heading')} ({suggestions.length})</h2>
            {suggestions.length === 0 ? (
              <p>{t('linking.no_suggestions')}</p>
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
                  const linkTooltip = buildLinkTooltip(link, t);
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
                          title={t('linking.confirm_suggestion_title')}
                        >
                          {t('linking.confirm')}
                        </button>
                        <button
                          className="btn-secondary"
                          onClick={() => handleRejectLink(link)}
                          disabled={!canEdit || isSaving}
                          title={t('linking.reject_suggestion_title')}
                        >
                          {t('linking.reject')}
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
