import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';

import { Language } from '../App';
import Modal from '../components/common/Modal';
import { useAuth } from '../contexts/AuthContext';
import { fullAudioUrl, listAudioForForm } from '../services/audioService';
import documentService from '../services/documentService';
import learnService, {
  DifficultyRating,
  KNOWN_SCORE_THRESHOLD,
} from '../services/learnService';
import wordService, { TranslationLink } from '../services/wordService';
import { TextWithLinks, TextWordLink } from '../types/text';
import './GuidedReader.css';

interface GuidedReaderProps {
  selectedLanguage: Language;
  languages: Language[];
}

/** A confirmed link plus its render span, sorted by position. */
interface Segment {
  key: string;
  content: string;
  link?: TextWordLink;
}

interface GlossState {
  link: TextWordLink;
  translations: TranslationLink[] | null; // null while loading
  audioUrl: string | null;
}

/** Where to render the gloss popover, relative to the text container. */
interface GlossAnchor {
  top: number;
  left: number;
  /** Render above the word when it sits near the bottom of the viewport. */
  placeAbove: boolean;
}

const GLOSS_WIDTH = 340;

const DIFFICULTY_OPTIONS: { value: DifficultyRating; label: string; hint: string }[] = [
  { value: 'easy', label: 'Easy', hint: 'Give me more new words next time' },
  { value: 'just_right', label: 'Just right', hint: 'Keep this pace' },
  { value: 'challenging', label: 'Challenging', hint: 'Fewer new words, please' },
  { value: 'too_hard', label: 'Too hard', hint: 'I need to consolidate first' },
];

/**
 * Legentibus-style guided reading: the text rendered as tappable word spans.
 * Tapping shows a gloss (translation, IPA, audio) and — for signed-in
 * learners — records a "don't know yet" signal. Finishing asks how hard it
 * was, which tunes how many new words the next recommendation may contain.
 */
export default function GuidedReader({ selectedLanguage }: GuidedReaderProps) {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();

  const [text, setText] = useState<TextWithLinks | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [knownLexemes, setKnownLexemes] = useState<Set<string>>(new Set());
  const [gloss, setGloss] = useState<GlossState | null>(null);
  const [glossAnchor, setGlossAnchor] = useState<GlossAnchor | null>(null);
  const [showDifficulty, setShowDifficulty] = useState(false);
  const [finished, setFinished] = useState(false);
  const [saving, setSaving] = useState(false);

  const contentRef = useRef<HTMLElement | null>(null);
  // Lexemes tapped during this session — excluded from the completion bonus.
  const clickedRef = useRef<Set<string>>(new Set());
  const glossCacheRef = useRef<Map<string, { translations: TranslationLink[]; audioUrl: string | null }>>(
    new Map(),
  );
  const playerRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!documentId) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    setGloss(null);
    setFinished(false);
    clickedRef.current = new Set();

    const load = async () => {
      try {
        const doc = await documentService.getWithLinks(documentId);
        if (cancelled) return;
        const match =
          doc.texts.find((t) => t.language_id === selectedLanguage.id) ??
          doc.texts.find((t) => t.is_primary) ??
          doc.texts[0];
        if (!match) {
          setError('This document has no readable text yet.');
          return;
        }
        setText(match);
      } catch (err: any) {
        if (!cancelled) {
          setError(err.response?.data?.detail || 'Failed to load the text.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [documentId, selectedLanguage.id]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    learnService
      .getWordKnowledge(selectedLanguage.id)
      .then((rows) => {
        if (cancelled) return;
        setKnownLexemes(
          new Set(
            rows.filter((r) => r.score >= KNOWN_SCORE_THRESHOLD).map((r) => r.lexeme_id),
          ),
        );
      })
      .catch(() => {
        // Highlighting is decoration; reading works without it.
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, selectedLanguage.id]);

  const confirmedLinks = useMemo(
    () =>
      (text?.word_links ?? [])
        .filter((l) => l.status === 'confirmed')
        .sort((a, b) => a.start_char - b.start_char),
    [text],
  );

  const segments: Segment[] = useMemo(() => {
    if (!text) return [];
    const out: Segment[] = [];
    let cursor = 0;
    confirmedLinks.forEach((link) => {
      if (link.start_char > cursor) {
        out.push({ key: `plain-${cursor}`, content: text.content.slice(cursor, link.start_char) });
      }
      out.push({
        key: `link-${link.id}`,
        content: text.content.slice(link.start_char, link.end_char),
        link,
      });
      cursor = link.end_char;
    });
    if (cursor < text.content.length) {
      out.push({ key: `plain-${cursor}`, content: text.content.slice(cursor) });
    }
    return out;
  }, [text, confirmedLinks]);

  const newWords = useMemo(() => {
    const seen = new Set<string>();
    const words: { lexemeId: string; label: string }[] = [];
    confirmedLinks.forEach((link) => {
      const lexemeId = link.lexeme_id ?? undefined;
      if (!lexemeId || seen.has(lexemeId) || knownLexemes.has(lexemeId)) return;
      seen.add(lexemeId);
      words.push({ lexemeId, label: link.word_lemma || link.word_text || '' });
    });
    return words;
  }, [confirmedLinks, knownLexemes]);

  /** Anchor the popover to the tapped word: below it, flipped above when the
   *  word sits in the bottom part of the viewport, clamped horizontally. */
  function anchorFor(wordEl: HTMLElement): GlossAnchor {
    const container = contentRef.current;
    if (!container) return { top: 0, left: 0, placeAbove: false };
    const word = wordEl.getBoundingClientRect();
    const box = container.getBoundingClientRect();
    const placeAbove = word.bottom > window.innerHeight - 260;
    const left = Math.max(0, Math.min(word.left - box.left, box.width - GLOSS_WIDTH));
    return {
      top: (placeAbove ? word.top - box.top : word.bottom - box.top) + (placeAbove ? -8 : 8),
      left,
      placeAbove,
    };
  }

  async function openGloss(link: TextWordLink, wordEl: HTMLElement) {
    playerRef.current?.pause();
    setGlossAnchor(anchorFor(wordEl));
    const lexemeId = link.lexeme_id ?? undefined;

    // Record the "don't know yet" signal once per lexeme per session.
    if (isAuthenticated && lexemeId && !clickedRef.current.has(lexemeId)) {
      clickedRef.current.add(lexemeId);
      learnService.clickWord(lexemeId).catch(() => {
        clickedRef.current.delete(lexemeId);
      });
    } else if (lexemeId) {
      clickedRef.current.add(lexemeId);
    }

    const cached = lexemeId ? glossCacheRef.current.get(lexemeId) : undefined;
    if (cached) {
      setGloss({ link, ...cached });
      return;
    }
    setGloss({ link, translations: null, audioUrl: null });
    const [translations, audioUrl] = await Promise.all([
      lexemeId ? wordService.listTranslations(lexemeId).catch(() => []) : Promise.resolve([]),
      listAudioForForm(link.word_form_id)
        .then((audios) => (audios.length > 0 ? fullAudioUrl(audios[0].file_path) : null))
        .catch(() => null),
    ]);
    if (lexemeId) glossCacheRef.current.set(lexemeId, { translations, audioUrl });
    setGloss((current) =>
      current && current.link.id === link.id ? { link, translations, audioUrl } : current,
    );
  }

  function playGlossAudio(url: string) {
    if (!playerRef.current || playerRef.current.src !== url) {
      playerRef.current?.pause();
      playerRef.current = new Audio(url);
    }
    void playerRef.current.play();
  }

  async function submitDifficulty(rating: DifficultyRating) {
    if (!text) return;
    setSaving(true);
    try {
      await learnService.completeText(text.id, rating, Array.from(clickedRef.current));
      setShowDifficulty(false);
      setFinished(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save your progress.');
      setShowDifficulty(false);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="reader-page">
        <div className="loading-state">Loading text…</div>
      </div>
    );
  }

  if (error && !text) {
    return (
      <div className="reader-page">
        <div className="error-state">{error}</div>
      </div>
    );
  }

  if (!text) return null;

  return (
    <div className="reader-page">
      <div className="reader-header">
        <button className="btn-link" onClick={() => navigate(-1)}>
          ← Back
        </button>
        <h1 className="reader-title">{text.title}</h1>
        <p className="reader-subtitle">
          Tap any word to see what it means{isAuthenticated ? ' — that also tells us which words to keep practising with you' : ''}.
        </p>
      </div>

      {newWords.length > 0 && isAuthenticated && (
        <div className="reader-new-words">
          <span className="reader-new-words-label">
            {newWords.length} new word{newWords.length === 1 ? '' : 's'} in this text:
          </span>
          {newWords.map((w) => (
            <span key={w.lexemeId} className="reader-new-word-chip">
              {w.label}
            </span>
          ))}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <article
        className="reader-content"
        lang={selectedLanguage.iso || undefined}
        ref={contentRef}
      >
        {segments.map((seg) =>
          seg.link ? (
            <button
              key={seg.key}
              type="button"
              className={`reader-word ${
                seg.link.lexeme_id && !knownLexemes.has(seg.link.lexeme_id) && isAuthenticated
                  ? 'reader-word-new'
                  : ''
              } ${gloss?.link.id === seg.link.id ? 'reader-word-active' : ''}`}
              onClick={(e) => void openGloss(seg.link!, e.currentTarget)}
            >
              {seg.content}
            </button>
          ) : (
            <span key={seg.key}>{seg.content}</span>
          ),
        )}

        {/* Gloss popover, anchored to the tapped word */}
        {gloss && glossAnchor && (
          <div
            className={`reader-gloss ${glossAnchor.placeAbove ? 'reader-gloss-above' : ''}`}
            style={{ top: glossAnchor.top, left: glossAnchor.left, width: GLOSS_WIDTH }}
            role="dialog"
            aria-label="Word details"
          >
            <div className="reader-gloss-head">
              <div>
                <span className="reader-gloss-word">
                  {gloss.link.word_lemma || gloss.link.word_text}
                </span>
                {gloss.link.word_form_ipa && (
                  <span className="reader-gloss-ipa">[{gloss.link.word_form_ipa}]</span>
                )}
                {gloss.link.word_part_of_speech && (
                  <span className="reader-gloss-pos">{gloss.link.word_part_of_speech}</span>
                )}
              </div>
              <button
                type="button"
                className="reader-gloss-close"
                onClick={() => setGloss(null)}
                aria-label="Close word details"
              >
                ✕
              </button>
            </div>
            <div className="reader-gloss-body">
              {gloss.translations === null && (
                <span className="reader-gloss-loading">Loading…</span>
              )}
              {gloss.translations !== null && gloss.translations.length === 0 && (
                <span className="reader-gloss-none">No translation recorded yet.</span>
              )}
              {gloss.translations !== null && gloss.translations.length > 0 && (
                <ul className="reader-gloss-translations">
                  {gloss.translations.map((tr) => (
                    <li key={tr.id}>
                      <b>{tr.lemma}</b>
                      {tr.language_name && <span> · {tr.language_name}</span>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="reader-gloss-actions">
              {gloss.audioUrl && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => playGlossAudio(gloss.audioUrl!)}
                >
                  ▶ Hear it
                </button>
              )}
              {gloss.link.lexeme_id && (
                <Link to={`/words/${gloss.link.lexeme_id}`} className="reader-gloss-more">
                  Full entry →
                </Link>
              )}
            </div>
          </div>
        )}
      </article>

      {/* ---------- Completion ---------- */}
      <div className="reader-footer">
        {finished ? (
          <div className="reader-finished">
            <p>Progress saved — your next text will match how this one felt.</p>
            <Link to="/learn" className="btn btn-accent">
              Continue learning
            </Link>
          </div>
        ) : isAuthenticated ? (
          <button
            type="button"
            className="btn btn-accent btn-lg"
            onClick={() => setShowDifficulty(true)}
          >
            I finished this text
          </button>
        ) : (
          <div className="reader-guest-cta">
            <p>
              Enjoying it?{' '}
              <Link to="/register" state={{ from: location }}>
                Create a free account
              </Link>{' '}
              to track the words you know and get the right next text.
            </p>
          </div>
        )}
      </div>

      <Modal
        isOpen={showDifficulty}
        onClose={() => setShowDifficulty(false)}
        title="How difficult was this text?"
      >
        <div className="reader-difficulty">
          {DIFFICULTY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className="reader-difficulty-option"
              disabled={saving}
              onClick={() => void submitDifficulty(opt.value)}
            >
              <span className="reader-difficulty-label">{opt.label}</span>
              <span className="reader-difficulty-hint">{opt.hint}</span>
            </button>
          ))}
        </div>
      </Modal>
    </div>
  );
}
