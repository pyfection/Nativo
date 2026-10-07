import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import AudioRecorder from '../components/common/AudioRecorder';
import { useAuth } from '../contexts/AuthContext';
import { AudioListItem } from '../services/audioService';
import contributeService, {
  ConfirmLinkTask,
  ContributeTask,
  DefineWordAnswer,
  DefineWordTask,
  RecordAudioTask,
  ReviewWordTask,
  TextContext,
  VoteTask,
} from '../services/contributeService';
import proposalService from '../services/proposalService';
import wordLinkService from '../services/wordLinkService';
import wordService, { TranslationLink } from '../services/wordService';
import { TextWordLinkStatus } from '../types/text';
import { languageDisplayName } from '../utils/languageName';
import './Contribute.css';

interface ContributeProps {
  selectedLanguage: Language;
  languages: Language[];
}

const DAILY_GOAL = 5;
const TODAY_KEY = 'nativo_contribute_today';
// Top up the deck when this few cards are left, so the next is always there.
const REFILL_AT = 2;

const PARTS_OF_SPEECH = [
  'noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction',
  'interjection', 'article', 'determiner', 'particle', 'numeral', 'other',
];

// Cards answered with yes / no (keys y / n).
type BinaryTask = ConfirmLinkTask | ReviewWordTask | VoteTask;
const isBinary = (task: ContributeTask): task is BinaryTask =>
  task.type === 'confirm_link' || task.type === 'review_word' || task.type === 'vote';

const isTyping = (target: EventTarget | null) =>
  target instanceof HTMLElement &&
  (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable);

// Today's count is a per-browser nicety, so localStorage is fine (and may be
// unavailable: private windows, blocked storage).
const localDate = () => new Date().toLocaleDateString('en-CA');
function readToday(): number {
  try {
    const saved = JSON.parse(localStorage.getItem(TODAY_KEY) || 'null');
    return saved?.date === localDate() ? Number(saved.count) || 0 : 0;
  } catch {
    return 0;
  }
}
function writeToday(count: number) {
  try {
    localStorage.setItem(TODAY_KEY, JSON.stringify({ date: localDate(), count }));
  } catch {
    // Not saving the counter is harmless.
  }
}

/**
 * Quick Contribute: one small task at a time, drawn from what the language
 * is missing (unknown words in texts, unrecorded words, unconfirmed links,
 * pending suggestions, open votes). Each card takes seconds; skip anything.
 */
export default function Contribute({ selectedLanguage, languages }: ContributeProps) {
  const { t } = useTranslation();
  const { user, canEditLanguage } = useAuth();
  const [queue, setQueue] = useState<ContributeTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [exhausted, setExhausted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [flash, setFlash] = useState('');
  const [sessionDone, setSessionDone] = useState(0);
  const [today, setToday] = useState(readToday);
  const skipped = useRef<string[]>([]);
  const fetching = useRef(false);
  const languageId = useRef(selectedLanguage.id);
  languageId.current = selectedLanguage.id;

  const canEdit = canEditLanguage(selectedLanguage.id);
  // Auto-promotion lives on the membership row, so it needs a join first.
  const isMember = !!user?.language_proficiencies?.some(
    (lp) => lp.language_id === selectedLanguage.id,
  );
  const glossLanguage = languages.find(
    (lang) => (lang.iso === 'eng' || lang.name === 'English') && lang.id !== selectedLanguage.id,
  );

  // Fresh deck per language.
  useEffect(() => {
    let cancelled = false;
    skipped.current = [];
    setQueue([]);
    setLoading(true);
    setExhausted(false);
    setError('');
    contributeService
      .getTasks(selectedLanguage.id, [])
      .then((tasks) => {
        if (cancelled) return;
        setQueue(tasks);
        setExhausted(tasks.length === 0);
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || t('contribute.load_failed'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id, t]);

  // Top up before the deck runs dry. Cards already queued or skipped are
  // excluded; done cards don't come back because their gap is filled.
  useEffect(() => {
    if (loading || exhausted || queue.length > REFILL_AT || fetching.current) return;
    fetching.current = true;
    const requestedFor = selectedLanguage.id;
    contributeService
      .getTasks(requestedFor, [...skipped.current, ...queue.map((task) => task.key)])
      .then((more) => {
        if (requestedFor !== languageId.current) return;
        setQueue((prev) => {
          const seen = new Set(prev.map((task) => task.key));
          return [...prev, ...more.filter((task) => !seen.has(task.key))];
        });
        if (more.length === 0) setExhausted(true);
      })
      .catch(() => setExhausted(true))
      .finally(() => {
        fetching.current = false;
      });
  }, [queue, loading, exhausted, selectedLanguage.id]);

  useEffect(() => {
    if (!flash) return;
    const timer = window.setTimeout(() => setFlash(''), 2500);
    return () => window.clearTimeout(timer);
  }, [flash]);

  const current = queue[0];

  const drop = (task: ContributeTask) => {
    setQueue((prev) => prev.filter((other) => other.key !== task.key));
    setError('');
  };

  const complete = (task: ContributeTask, message: string) => {
    const next = today + 1;
    setToday(next);
    writeToday(next);
    setSessionDone((n) => n + 1);
    setFlash(next === DAILY_GOAL ? t('contribute.goal_reached', { goal: DAILY_GOAL }) : message);
    drop(task);
  };

  const skip = (task: ContributeTask) => {
    skipped.current.push(task.key);
    drop(task);
  };

  const run = async (task: ContributeTask, action: () => Promise<unknown>, message: string) => {
    setBusy(true);
    setError('');
    try {
      await action();
      complete(task, message);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('contribute.action_failed'));
    } finally {
      setBusy(false);
    }
  };

  const answer = (task: BinaryTask, yes: boolean) => {
    switch (task.type) {
      case 'confirm_link':
        return run(
          task,
          () =>
            wordLinkService.update(task.context.text_id, task.link_id, {
              status: yes ? TextWordLinkStatus.CONFIRMED : TextWordLinkStatus.REJECTED,
            }),
          yes ? t('contribute.done_link_confirmed') : t('contribute.done_link_rejected'),
        );
      case 'review_word':
        return run(
          task,
          () => (yes ? wordService.verify(task.lexeme_id) : wordService.reject(task.lexeme_id)),
          yes ? t('contribute.done_review_approved') : t('contribute.done_review_rejected'),
        );
      case 'vote':
        return run(
          task,
          () => proposalService.vote(task.proposal.id, yes ? 'approve' : 'reject'),
          t('contribute.done_vote'),
        );
    }
  };

  const define = (task: DefineWordTask, data: DefineWordAnswer) =>
    run(
      task,
      () => contributeService.defineWord(selectedLanguage.id, data),
      canEdit ? t('contribute.done_define_published') : t('contribute.done_define_suggested'),
    );

  // y / n answer the yes-no cards, s skips. Re-bound every render so the
  // handler sees the current card.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!current || busy || isTyping(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === 's') skip(current);
      else if (isBinary(current) && (e.key === 'y' || e.key === 'n')) void answer(current, e.key === 'y');
      else return;
      e.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const restart = () => {
    skipped.current = [];
    setExhausted(false);
  };

  const renderCard = (task: ContributeTask) => {
    switch (task.type) {
      case 'define_word':
        return (
          <DefineWordCard
            task={task}
            glossLanguage={glossLanguage}
            canEdit={canEdit}
            busy={busy}
            onSubmit={(data) => void define(task, data)}
          />
        );
      case 'record_audio':
        return (
          <RecordAudioCard
            task={task}
            onError={setError}
            onDone={() => complete(task, t('contribute.done_record_audio'))}
          />
        );
      case 'confirm_link':
        return <ConfirmLinkCard task={task} />;
      case 'review_word':
        return <ReviewWordCard task={task} />;
      case 'vote':
        return <VoteCard task={task} />;
    }
  };

  const goalPct = Math.min(100, (today / DAILY_GOAL) * 100);

  return (
    <div className="contribute-page">
      <div className="contribute-header">
        <h1>{t('contribute.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="contribute-subtitle">{t('contribute.subtitle')}</p>
      </div>

      <div className="contribute-progress" aria-live="polite">
        <div className="contribute-progress-bar">
          <div className="contribute-progress-fill" style={{ width: `${goalPct}%` }} />
        </div>
        <div className="contribute-progress-text">
          <span>{t('contribute.today', { count: today, goal: DAILY_GOAL })}</span>
          {sessionDone > 0 && <span>{t('contribute.session', { count: sessionDone })}</span>}
        </div>
      </div>

      {!canEdit && (
        <p className="contribute-note">
          {t('contribute.suggester_note')}
          {!isMember &&
            ` ${t('contribute.join_note', { language: languageDisplayName(selectedLanguage) })}`}
        </p>
      )}
      {flash && (
        <div className="contribute-flash" role="status">
          {flash}
        </div>
      )}
      {error && <div className="error-message">{error}</div>}
      {loading && <div className="loading-state">{t('contribute.loading')}</div>}

      {current && (
        <div className="contribute-card" key={current.key}>
          <div className="contribute-card-kind">{t(`contribute.kind_${current.type}`)}</div>
          {renderCard(current)}
          <div className="contribute-card-actions">
            {isBinary(current) && (
              <>
                <button
                  type="button"
                  className="contribute-btn-yes"
                  disabled={busy}
                  onClick={() => void answer(current, true)}
                >
                  {t(`contribute.yes_${current.type}`)} <kbd>y</kbd>
                </button>
                <button
                  type="button"
                  className="contribute-btn-no"
                  disabled={busy}
                  onClick={() => void answer(current, false)}
                >
                  {t(`contribute.no_${current.type}`)} <kbd>n</kbd>
                </button>
              </>
            )}
            <button
              type="button"
              className="btn btn-ghost contribute-skip"
              disabled={busy}
              onClick={() => skip(current)}
            >
              {t('contribute.skip')} <kbd>s</kbd>
            </button>
          </div>
        </div>
      )}

      {!loading && !current && exhausted && (
        <div className="contribute-empty">
          <h2>{t('contribute.empty_title')}</h2>
          <p>{t('contribute.empty_body')}</p>
          <div className="contribute-empty-actions">
            {skipped.current.length > 0 && (
              <button type="button" className="btn btn-accent" onClick={restart}>
                {t('contribute.show_skipped')}
              </button>
            )}
            <Link to="/words/add" className="btn btn-ghost">
              {t('contribute.empty_add_word')}
            </Link>
            <Link to="/documents/add" className="btn btn-ghost">
              {t('contribute.empty_add_text')}
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Pieces shared by the cards ---------- */

function Snippet({ context }: { context: TextContext }) {
  // Offsets come from Python (code points), so slice by code point too.
  const chars = Array.from(context.snippet);
  const { highlight_start: start, highlight_end: end } = context;
  return (
    <figure className="contribute-snippet">
      <blockquote>
        {chars.slice(0, start).join('')}
        <mark>{chars.slice(start, end).join('')}</mark>
        {chars.slice(end).join('')}
      </blockquote>
      <figcaption>
        {context.document_id ? (
          <Link to={`/documents/${context.document_id}`}>{context.title}</Link>
        ) : (
          context.title
        )}
      </figcaption>
    </figure>
  );
}

function Meanings({ translations }: { translations: TranslationLink[] }) {
  const { t } = useTranslation();
  if (translations.length === 0) {
    return <p className="contribute-meta">{t('contribute.no_translations')}</p>;
  }
  return (
    <p className="contribute-translations">{translations.map((tr) => tr.lemma).join(', ')}</p>
  );
}

/* ---------- Cards ---------- */

interface DefineWordCardProps {
  task: DefineWordTask;
  glossLanguage?: Language;
  canEdit: boolean;
  busy: boolean;
  onSubmit: (data: DefineWordAnswer) => void;
}

function DefineWordCard({ task, glossLanguage, canEdit, busy, onSubmit }: DefineWordCardProps) {
  const { t } = useTranslation();
  const [lemma, setLemma] = useState(task.token);
  const [gloss, setGloss] = useState('');
  const [pos, setPos] = useState('');

  const ready = lemma.trim() && (!glossLanguage || gloss.trim());

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!ready || busy) return;
    onSubmit({
      token: task.token,
      lemma: lemma.trim(),
      part_of_speech: pos || undefined,
      gloss: gloss.trim() || undefined,
      gloss_language_id: gloss.trim() ? glossLanguage?.id : undefined,
    });
  };

  return (
    <form className="contribute-define" onSubmit={submit}>
      <p className="contribute-question">
        {t('contribute.define_question', { word: task.token })}
      </p>
      <Snippet context={task.context} />
      {task.occurrences > 1 && (
        <p className="contribute-meta">
          {t('contribute.define_occurrences', { count: task.occurrences })}
        </p>
      )}
      {glossLanguage && (
        <label className="contribute-field">
          <span>
            {t('contribute.define_gloss_label', { language: languageDisplayName(glossLanguage) })}
          </span>
          <input
            autoFocus
            value={gloss}
            onChange={(e) => setGloss(e.target.value)}
            placeholder={t('contribute.define_gloss_placeholder')}
          />
        </label>
      )}
      <div className="contribute-field-row">
        <label className="contribute-field">
          <span>{t('contribute.define_lemma_label')}</span>
          <input value={lemma} onChange={(e) => setLemma(e.target.value)} />
        </label>
        <label className="contribute-field">
          <span>{t('contribute.define_pos_label')}</span>
          <select value={pos} onChange={(e) => setPos(e.target.value)}>
            <option value="">{t('add_word.select_placeholder')}</option>
            {PARTS_OF_SPEECH.map((value) => (
              <option key={value} value={value}>
                {t(`add_word.pos_${value}`)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="contribute-hint">{t('contribute.define_lemma_hint')}</p>
      <button type="submit" className="btn btn-accent" disabled={!ready || busy}>
        {canEdit ? t('contribute.define_add') : t('contribute.define_suggest')}
      </button>
    </form>
  );
}

interface RecordAudioCardProps {
  task: RecordAudioTask;
  onError: (message: string) => void;
  onDone: () => void;
}

function RecordAudioCard({ task, onError, onDone }: RecordAudioCardProps) {
  const { t } = useTranslation();
  const [recorded, setRecorded] = useState(false);
  // Stable: AudioRecorder re-fetches its list whenever this changes.
  const handleChange = useCallback((audios: AudioListItem[]) => {
    if (audios.length > 0) setRecorded(true);
  }, []);

  return (
    <div className="contribute-record">
      <p className="contribute-question">{t('contribute.audio_question')}</p>
      <div className="contribute-word">{task.form}</div>
      {task.ipa_pronunciation && (
        <div className="contribute-ipa">/{task.ipa_pronunciation}/</div>
      )}
      <Meanings translations={task.translations} />
      {task.uses > 0 && (
        <p className="contribute-meta">{t('contribute.audio_uses', { count: task.uses })}</p>
      )}
      <AudioRecorder wordFormId={task.word_form_id} canEdit onChange={handleChange} onError={onError} />
      {recorded && (
        <button type="button" className="btn btn-accent" onClick={onDone}>
          {t('contribute.next')}
        </button>
      )}
    </div>
  );
}

function ConfirmLinkCard({ task }: { task: ConfirmLinkTask }) {
  const { t } = useTranslation();
  return (
    <div className="contribute-link">
      <Snippet context={task.context} />
      <p className="contribute-question">{t('contribute.link_question', { lemma: task.lemma })}</p>
      <Meanings translations={task.translations} />
    </div>
  );
}

function ReviewWordCard({ task }: { task: ReviewWordTask }) {
  const { t } = useTranslation();
  return (
    <div className="contribute-review">
      <p className="contribute-question">{t('contribute.review_question')}</p>
      <div className="contribute-word">{task.lemma}</div>
      <div className="contribute-meta">
        {task.part_of_speech && <span>{t(`add_word.pos_${task.part_of_speech}`)}</span>}
        {task.ipa_pronunciation && <span> · /{task.ipa_pronunciation}/</span>}
      </div>
      <Meanings translations={task.translations} />
      {task.notes && <p className="contribute-notes">{task.notes}</p>}
      <p className="contribute-meta">
        {task.creator_username && t('review.suggested_by', { username: task.creator_username })}
        {' · '}
        <Link to="/review">{t('contribute.review_edit_link')}</Link>
      </p>
    </div>
  );
}

function VoteCard({ task }: { task: VoteTask }) {
  const { t } = useTranslation();
  const { proposal } = task;
  return (
    <div className="contribute-vote">
      <p className="contribute-question">
        {t('contribute.vote_question', {
          recommendation: t(`word_detail.recommendation_${proposal.payload.recommendation}`),
        })}
      </p>
      <div className="contribute-word">
        {proposal.lexeme_id ? (
          <Link to={`/words/${proposal.lexeme_id}#proposals`}>{proposal.lexeme_lemma}</Link>
        ) : (
          proposal.lexeme_lemma
        )}
      </div>
      {proposal.rationale && <p className="contribute-notes">{proposal.rationale}</p>}
      {proposal.usage.length > 0 && (
        <ul className="contribute-usage">
          {proposal.usage.map((usage) => (
            <li key={usage.lexeme_id}>
              <strong>{usage.lemma}</strong>{' '}
              {t('contribute.vote_usage', { texts: usage.text_count, audio: usage.audio_count })}
            </li>
          ))}
        </ul>
      )}
      <p className="contribute-meta">
        {t('word_detail.tally_approvals', { count: proposal.approvals, threshold: proposal.threshold })}
        {' · '}
        {t('word_detail.tally_objections', { count: proposal.rejections })}
      </p>
    </div>
  );
}
