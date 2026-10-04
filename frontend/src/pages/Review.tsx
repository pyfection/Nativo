import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import WordReviewCard from '../components/review/WordReviewCard';
import { useAuth } from '../contexts/AuthContext';
import documentService, { TextSuggestion } from '../services/documentService';
import proposalService, { ChangeProposal } from '../services/proposalService';
import wordService, { LexemeSuggestion, ReviewCorrections } from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
import './Review.css';

interface ReviewProps {
  selectedLanguage: Language;
  languages: Language[];
}

// Drafted batches carry a confidence; group the queue by it so the safe ones
// can be approved in bulk and attention goes to the uncertain ones.
const GROUPS = ['high', 'medium', 'low', 'none'] as const;
type Group = (typeof GROUPS)[number];
const groupOf = (item: LexemeSuggestion): Group => item.draft_confidence ?? 'none';

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement &&
  (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable);

/**
 * The reviewer's queue: word and text suggestions from non-editors awaiting
 * a verdict. Approve publishes (and, for words, can auto-promote a trusted
 * suggester to editor); reject archives with an optional reason. Words can
 * be corrected inline and approved in one step, and the whole word queue is
 * keyboard-driven: j/k move, a approve, e edit, r reject.
 */
export default function Review({ selectedLanguage, languages }: ReviewProps) {
  const { t } = useTranslation();
  const { canVerifyLanguage } = useAuth();
  const [words, setWords] = useState<LexemeSuggestion[]>([]);
  const [texts, setTexts] = useState<TextSuggestion[]>([]);
  const [proposals, setProposals] = useState<ChangeProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number } | null>(null);
  const cardRefs = useRef(new Map<string, HTMLLIElement>());

  const canVerify = canVerifyLanguage(selectedLanguage.id);

  // Words in queue order: grouped by confidence, oldest first within a group.
  const ordered = useMemo(
    () => GROUPS.flatMap((group) => words.filter((w) => groupOf(w) === group)),
    [words],
  );

  // Glosses are edited in the languages a word already has, plus English as
  // the default gloss language when it has none.
  const english = languages.find((lang) => lang.iso === 'eng' || lang.name === 'English');
  const glossLanguagesFor = (item: LexemeSuggestion) => {
    const ids = new Set(item.translations.map((tr) => tr.language_id));
    if (english && english.id !== selectedLanguage.id) ids.add(english.id);
    return languages.filter((lang) => ids.has(lang.id));
  };

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [wordData, textData, proposalData] = await Promise.all([
        wordService.listSuggestions(selectedLanguage.id),
        documentService.listSuggestions(selectedLanguage.id),
        proposalService.listOpen(selectedLanguage.id).catch(() => []),
      ]);
      setWords(wordData);
      setTexts(textData);
      setProposals(proposalData);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.load_failed'));
    } finally {
      setLoading(false);
    }
  }, [selectedLanguage.id, t]);

  useEffect(() => {
    if (canVerify) void refresh();
  }, [canVerify, refresh]);

  const promptReason = () =>
    window.prompt(t('review.reject_reason_prompt')) || undefined;

  /** Drop a settled word and move focus to whatever now sits in its place. */
  const settle = (id: string) => {
    const index = ordered.findIndex((w) => w.id === id);
    const rest = ordered.filter((w) => w.id !== id);
    setWords((prev) => prev.filter((item) => item.id !== id));
    setEditingId(null);
    setActiveId(rest.length ? rest[Math.min(index, rest.length - 1)].id : null);
  };

  const approveWord = async (id: string, corrections?: ReviewCorrections) => {
    try {
      setBusyId(id);
      setError('');
      const hasFixes = corrections && Object.keys(corrections).length > 0;
      await wordService.verify(id, hasFixes ? corrections : undefined);
      settle(id);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.action_failed'));
    } finally {
      setBusyId(null);
    }
  };

  const rejectWord = async (id: string) => {
    const reason = promptReason();
    try {
      setBusyId(id);
      setError('');
      await wordService.reject(id, reason);
      settle(id);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.action_failed'));
    } finally {
      setBusyId(null);
    }
  };

  const approveGroup = async (group: Group) => {
    const batch = words.filter((w) => groupOf(w) === group);
    if (!window.confirm(t('review.approve_all_confirm', { count: batch.length }))) return;
    setError('');
    setBulkProgress({ done: 0, total: batch.length });
    const approved = new Set<string>();
    for (const item of batch) {
      try {
        await wordService.verify(item.id);
        approved.add(item.id);
      } catch (err: any) {
        setError(err.response?.data?.detail || t('review.action_failed'));
        break;
      }
      setBulkProgress({ done: approved.size, total: batch.length });
    }
    setWords((prev) => prev.filter((item) => !approved.has(item.id)));
    setBulkProgress(null);
  };

  // Keyboard review. Re-bound on every render so handlers see fresh state.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (editingId || busyId || bulkProgress || isTyping(e.target)) return;
      if (e.ctrlKey || e.metaKey || e.altKey || ordered.length === 0) return;
      const index = Math.max(0, ordered.findIndex((w) => w.id === activeId));
      const current = ordered[index];
      const move = (delta: number) => {
        const next = ordered[Math.min(ordered.length - 1, Math.max(0, index + delta))];
        setActiveId(next.id);
      };
      switch (e.key) {
        case 'j':
        case 'ArrowDown':
          move(activeId ? 1 : 0);
          break;
        case 'k':
        case 'ArrowUp':
          move(-1);
          break;
        case 'a':
          void approveWord(current.id);
          break;
        case 'e':
          setActiveId(current.id);
          setEditingId(current.id);
          break;
        case 'r':
          void rejectWord(current.id);
          break;
        default:
          return;
      }
      e.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  useEffect(() => {
    if (activeId) cardRefs.current.get(activeId)?.scrollIntoView({ block: 'nearest' });
  }, [activeId]);

  if (!canVerify) {
    return (
      <div className="review-page">
        <h1>{t('review.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="review-no-permission">{t('review.no_permission')}</p>
      </div>
    );
  }

  const actOnText = async (item: TextSuggestion, action: 'approve' | 'reject') => {
    if (!item.document_id) return;
    const reason = action === 'reject' ? promptReason() : undefined;
    try {
      setBusyId(item.id);
      if (action === 'approve') await documentService.approveText(item.document_id, item.id);
      else await documentService.rejectText(item.document_id, item.id, reason);
      setTexts((prev) => prev.filter((other) => other.id !== item.id));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.action_failed'));
    } finally {
      setBusyId(null);
    }
  };

  const actions = (id: string, onAct: (action: 'approve' | 'reject') => void) => (
    <div className="review-item-actions">
      <button
        type="button"
        className="btn-approve"
        disabled={busyId === id}
        onClick={() => onAct('approve')}
      >
        {t('review.approve')}
      </button>
      <button
        type="button"
        className="btn-reject"
        disabled={busyId === id}
        onClick={() => onAct('reject')}
      >
        {t('review.reject')}
      </button>
    </div>
  );

  const empty =
    !loading && words.length === 0 && texts.length === 0 && proposals.length === 0;

  return (
    <div className="review-page">
      <div className="review-header">
        <h1>{t('review.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="review-subtitle">{t('review.subtitle')}</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {loading && <div className="loading-state">{t('review.loading')}</div>}

      {empty && <div className="review-empty">{t('review.empty')}</div>}

      {proposals.length > 0 && (
        <section className="review-section">
          <h2 className="review-section-title">{t('review.proposals_heading')}</h2>
          <ul className="review-list">
            {proposals.map((p) => (
              <li key={p.id} className="review-item">
                <div className="review-item-main">
                  <Link to={`/words/${p.lexeme_id}#proposals`} className="review-item-lemma">
                    {p.lexeme_lemma}
                  </Link>
                  <span className="review-item-pos">
                    {t('word_detail.proposal_title', {
                      recommendation: t(`word_detail.recommendation_${p.payload.recommendation}`),
                    })}
                  </span>
                </div>
                <div className="review-item-meta">
                  <span>
                    {t('word_detail.tally_approvals', { count: p.approvals, threshold: p.threshold })}
                    {' · '}
                    {t('word_detail.tally_objections', { count: p.rejections })}
                  </span>
                  {p.created_by_username && (
                    <span>{t('review.suggested_by', { username: p.created_by_username })}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {words.length > 0 && (
        <section className="review-section">
          <h2 className="review-section-title">{t('review.words_heading')}</h2>
          <p className="review-keyboard-hint">{t('review.keyboard_hint')}</p>
          {bulkProgress && (
            <div className="loading-state">
              {t('review.approving_progress', bulkProgress)}
            </div>
          )}
          {GROUPS.map((group) => {
            const items = ordered.filter((w) => groupOf(w) === group);
            if (items.length === 0) return null;
            return (
              <div key={group} className="review-group">
                <div className="review-group-header">
                  <h3>
                    {t(`review.group_${group}`)} <span>({items.length})</span>
                  </h3>
                  {group === 'high' && (
                    <button
                      type="button"
                      className="btn-approve"
                      disabled={!!bulkProgress || !!busyId}
                      onClick={() => void approveGroup(group)}
                    >
                      {t('review.approve_all', { count: items.length })}
                    </button>
                  )}
                </div>
                <ul className="review-list">
                  {items.map((item) => (
                    <WordReviewCard
                      key={item.id}
                      ref={(el) => {
                        if (el) cardRefs.current.set(item.id, el);
                        else cardRefs.current.delete(item.id);
                      }}
                      item={item}
                      active={activeId === item.id}
                      editing={editingId === item.id}
                      busy={busyId === item.id || !!bulkProgress}
                      glossLanguages={glossLanguagesFor(item)}
                      onFocus={() => setActiveId(item.id)}
                      onApprove={(corrections) => void approveWord(item.id, corrections)}
                      onReject={() => void rejectWord(item.id)}
                      onEdit={() => {
                        setActiveId(item.id);
                        setEditingId(item.id);
                      }}
                      onCancelEdit={() => setEditingId(null)}
                    />
                  ))}
                </ul>
              </div>
            );
          })}
        </section>
      )}

      {texts.length > 0 && (
        <section className="review-section">
          <h2 className="review-section-title">{t('review.texts_heading')}</h2>
          <ul className="review-list">
            {texts.map((item) => (
              <li key={item.id} className="review-item review-item-text">
                <div className="review-item-main">
                  {item.document_id ? (
                    <Link to={`/documents/${item.document_id}`} className="review-item-lemma">
                      {item.title}
                    </Link>
                  ) : (
                    <span className="review-item-lemma">{item.title}</span>
                  )}
                </div>
                <div className="review-item-meta">
                  {item.creator_username && (
                    <span>{t('review.suggested_by', { username: item.creator_username })}</span>
                  )}
                </div>
                {actions(item.id, (action) => void actOnText(item, action))}
                <p className="review-item-preview">
                  {item.content.length > 240 ? `${item.content.slice(0, 240)}…` : item.content}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
