import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import AudioRecorder from '../components/common/AudioRecorder';
import { useAuth } from '../contexts/AuthContext';
import { AudioListItem } from '../services/audioService';
import contributeService, {
  ConfirmLinkTask,
  ConfirmSpellingTask,
  ContributeResult,
  ContributeTask,
  DefineWordAnswer,
  DefineWordTask,
  RecordAudioTask,
  ReviewAdditionTask,
  ReviewWordTask,
  SourceContext,
  SpellingAnswer,
  TextContext,
  TranslateTextAnswer,
  TranslateTextTask,
  TranslateWordAnswer,
  TranslateWordTask,
  VoteTask,
  WordSuggestion,
  WordSuggestionQuery,
} from '../services/contributeService';
import { OutboxConfig, pendingKeys, QueuedOffline } from '../services/outbox';
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
type BinaryTask = ConfirmLinkTask | ReviewWordTask | VoteTask | ReviewAdditionTask;
const BINARY_TYPES: ContributeTask['type'][] = [
  'confirm_link',
  'review_word',
  'vote',
  'review_addition',
];
const isBinary = (task: ContributeTask): task is BinaryTask => BINARY_TYPES.includes(task.type);

/** The word or title a card is about, to name it in the offline banner. */
function cardSubject(task: ContributeTask): string {
  switch (task.type) {
    case 'define_word':
    case 'confirm_spelling':
      return task.token;
    case 'record_audio':
      return task.form;
    case 'vote':
      return task.proposal.lexeme_lemma ?? '';
    case 'translate_text':
      return task.title;
    default:
      return task.lemma;
  }
}

// Cards answered offline wait in the outbox; don't deal them again.
const notPending = (tasks: ContributeTask[]) => {
  const pending = pendingKeys();
  return tasks.filter((task) => !pending.has(task.key));
};

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
 * is missing (unknown words in texts and outside sources, unrecorded words,
 * unconfirmed links, untranslated words and texts from languages the user
 * speaks, pending suggestions, open votes). Each card takes seconds; skip
 * anything.
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
  // Translation cards come from the other languages the user has joined.
  const speaksOthers = !!user?.language_proficiencies?.some(
    (lp) => lp.language_id !== selectedLanguage.id,
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
        setQueue(notPending(tasks));
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
          return [...prev, ...notPending(more).filter((task) => !seen.has(task.key))];
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

  const outboxFor = (task: ContributeTask): OutboxConfig => ({
    outbox: {
      label: `${t(`contribute.kind_${task.type}`)}: ${cardSubject(task)}`,
      key: task.key,
    },
  });

  const run = async <T,>(
    task: ContributeTask,
    action: (config: OutboxConfig) => Promise<T>,
    message: string | ((result: T) => string),
  ) => {
    setBusy(true);
    setError('');
    try {
      const result = await action(outboxFor(task));
      complete(task, typeof message === 'function' ? message(result) : message);
    } catch (err: any) {
      if (err instanceof QueuedOffline) complete(task, t('offline.saved'));
      else setError(err.response?.data?.detail || t('contribute.action_failed'));
    } finally {
      setBusy(false);
    }
  };

  const answer = (task: BinaryTask, yes: boolean) => {
    switch (task.type) {
      case 'confirm_link':
        return run(
          task,
          (config) =>
            wordLinkService.update(
              task.context.text_id,
              task.link_id,
              { status: yes ? TextWordLinkStatus.CONFIRMED : TextWordLinkStatus.REJECTED },
              config,
            ),
          yes ? t('contribute.done_link_confirmed') : t('contribute.done_link_rejected'),
        );
      case 'review_word':
        return run(
          task,
          (config) =>
            yes
              ? wordService.verify(task.lexeme_id, undefined, config)
              : wordService.reject(task.lexeme_id, undefined, config),
          yes ? t('contribute.done_review_approved') : t('contribute.done_review_rejected'),
        );
      case 'vote':
        return run(
          task,
          (config) =>
            proposalService.vote(task.proposal.id, yes ? 'approve' : 'reject', undefined, config),
          t('contribute.done_vote'),
        );
      case 'review_addition':
        return run(
          task,
          (config) => proposalService.review(task.proposal_id, yes, config),
          yes ? t('contribute.done_review_approved') : t('contribute.done_review_rejected'),
        );
    }
  };

  const outcomeMessage = (result: ContributeResult) => t(`contribute.done_${result.outcome}`);

  const define = (task: DefineWordTask, data: DefineWordAnswer) =>
    run(
      task,
      (config) => contributeService.defineWord(selectedLanguage.id, data, config),
      (result) =>
        result.outcome === 'proposed'
          ? t('contribute.done_proposed')
          : t(`contribute.done_define_${result.outcome}`),
    );

  const confirmSpelling = (task: ConfirmSpellingTask, data: SpellingAnswer) =>
    run(task, (config) => contributeService.confirmSpelling(selectedLanguage.id, data, config), outcomeMessage);

  const translateWord = (task: TranslateWordTask, data: TranslateWordAnswer) =>
    run(task, (config) => contributeService.translateWord(selectedLanguage.id, data, config), outcomeMessage);

  const translateText = (task: TranslateTextTask, data: TranslateTextAnswer) =>
    run(task, (config) => contributeService.translateText(selectedLanguage.id, data, config), outcomeMessage);

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
            languageId={selectedLanguage.id}
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
            outbox={outboxFor(task).outbox!}
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
      case 'confirm_spelling':
        return (
          <ConfirmSpellingCard
            task={task}
            languageId={selectedLanguage.id}
            glossLanguage={glossLanguage}
            busy={busy}
            onSubmit={(data) => void confirmSpelling(task, data)}
          />
        );
      case 'translate_word':
        return (
          <TranslateWordCard
            task={task}
            languages={languages}
            targetLanguage={selectedLanguage}
            busy={busy}
            onSubmit={(data) => void translateWord(task, data)}
          />
        );
      case 'translate_text':
        return (
          <TranslateTextCard
            task={task}
            languages={languages}
            targetLanguage={selectedLanguage}
            busy={busy}
            onSubmit={(data) => void translateText(task, data)}
          />
        );
      case 'review_addition':
        return <ReviewAdditionCard task={task} languages={languages} />;
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
      {!speaksOthers && (
        <p className="contribute-note">
          {t('contribute.languages_note')}{' '}
          <Link to="/languages">{t('contribute.languages_link')}</Link>
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

function Highlighted({ text, start, end }: { text: string; start: number; end: number }) {
  // Offsets come from Python (code points), so slice by code point too.
  const chars = Array.from(text);
  return (
    <blockquote>
      {chars.slice(0, start).join('')}
      <mark>{chars.slice(start, end).join('')}</mark>
      {chars.slice(end).join('')}
    </blockquote>
  );
}

/** Credit line for outside content: linked title, plus its licence. */
function SourceCredit({ url, title, license }: { url: string; title: string; license: string | null }) {
  return (
    <>
      <a href={url} target="_blank" rel="noopener noreferrer">
        {title} ↗
      </a>
      {license && <span className="contribute-license"> · {license}</span>}
    </>
  );
}

function OutsideSnippet({ source }: { source: SourceContext }) {
  return (
    <figure className="contribute-snippet">
      <Highlighted
        text={source.snippet}
        start={source.highlight_start}
        end={source.highlight_end}
      />
      <figcaption>
        <SourceCredit url={source.source_url} title={source.source_title} license={source.license} />
      </figcaption>
    </figure>
  );
}

const languageName = (languages: Language[], id: string | null) => {
  const lang = languages.find((l) => l.id === id);
  return lang ? languageDisplayName(lang) : '';
};

function Snippet({ context }: { context: TextContext }) {
  return (
    <figure className="contribute-snippet">
      <Highlighted
        text={context.snippet}
        start={context.highlight_start}
        end={context.highlight_end}
      />
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

/** The AI's suggestion for a word card, or null while loading, when AI
 *  suggestions aren't set up, or offline. Suggestions are optional, so
 *  failures stay silent. */
function useWordSuggestion(languageId: string, query: WordSuggestionQuery): WordSuggestion | null {
  const [suggestion, setSuggestion] = useState<WordSuggestion | null>(null);
  const { token, text_id, snippet_id, gloss_language_id } = query;
  useEffect(() => {
    let cancelled = false;
    contributeService
      .suggestWord(languageId, { token, text_id, snippet_id, gloss_language_id })
      .then((result) => {
        if (!cancelled) setSuggestion(result);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [languageId, token, text_id, snippet_id, gloss_language_id]);
  return suggestion;
}

/** A field the AI pre-fills until the person edits it. `fromAi` marks a
 *  value that is still the AI's, so the card can say so. */
function useSuggestedField(initial: string, suggested: string | null | undefined) {
  const [value, setValue] = useState(initial);
  const [touched, setTouched] = useState(false);
  useEffect(() => {
    if (suggested && !touched) setValue(suggested);
  }, [suggested, touched]);
  return {
    value,
    fromAi: !!suggested && !touched && value === suggested,
    set: (next: string) => {
      setTouched(true);
      setValue(next);
    },
    /** Change the value without counting as the person's edit. */
    reset: setValue,
  };
}

function AiBadge() {
  const { t } = useTranslation();
  return (
    <span className="contribute-ai-badge" title={t('contribute.ai_title')}>
      ✨ {t('contribute.ai_badge')}
    </span>
  );
}

/* ---------- Cards ---------- */

interface DefineWordCardProps {
  task: DefineWordTask;
  languageId: string;
  glossLanguage?: Language;
  canEdit: boolean;
  busy: boolean;
  onSubmit: (data: DefineWordAnswer) => void;
}

function DefineWordCard({
  task,
  languageId,
  glossLanguage,
  canEdit,
  busy,
  onSubmit,
}: DefineWordCardProps) {
  const { t } = useTranslation();
  const suggestion = useWordSuggestion(languageId, {
    token: task.token,
    text_id: task.context.text_id,
    gloss_language_id: glossLanguage?.id,
  });
  const lemma = useSuggestedField(task.token, suggestion?.lemma);
  const gloss = useSuggestedField('', suggestion?.gloss);
  const pos = useSuggestedField('', suggestion?.part_of_speech);

  // "Spelled wrong?": the text's spelling is outdated or non-standard.
  const [fixDraft, setFixDraft] = useState<string | null>(null);
  const [corrected, setCorrected] = useState('');
  const [knownFix, setKnownFix] = useState(false); // corrected word already in the dictionary
  const fixRequest = useRef('');
  const word = corrected || task.token;

  const applyFix = () => {
    const value = (fixDraft ?? '').trim();
    setFixDraft(null);
    if (!value || value === task.token) return;
    setCorrected(value);
    if (lemma.value === task.token) lemma.reset(value);
    setKnownFix(false);
    fixRequest.current = value;
    wordService
      .resolveSpelling(languageId, value)
      .then((result) => {
        if (fixRequest.current === value) setKnownFix(result.already_standard);
      })
      .catch(() => undefined);
  };

  const undoFix = () => {
    fixRequest.current = '';
    if (lemma.value === corrected) lemma.reset(task.token);
    setCorrected('');
    setKnownFix(false);
  };

  const ready = knownFix || (lemma.value.trim() && (!glossLanguage || gloss.value.trim()));

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!ready || busy || fixDraft !== null) return;
    if (knownFix) {
      onSubmit({ token: task.token, corrected, lemma: corrected });
      return;
    }
    onSubmit({
      token: task.token,
      corrected: corrected || undefined,
      lemma: lemma.value.trim(),
      part_of_speech: pos.value || undefined,
      gloss: gloss.value.trim() || undefined,
      gloss_language_id: gloss.value.trim() ? glossLanguage?.id : undefined,
    });
  };

  return (
    <form className="contribute-define" onSubmit={submit}>
      <p className="contribute-question">{t('contribute.define_question', { word })}</p>
      <Snippet context={task.context} />

      {corrected ? (
        <p className="contribute-fix">
          {t('contribute.fix_summary', { from: task.token, to: corrected })}{' '}
          {canEdit ? t('contribute.fix_editor_note') : t('contribute.fix_reviewer_note')}{' '}
          <button type="button" className="contribute-link-btn" onClick={undoFix}>
            {t('contribute.fix_undo')}
          </button>
        </p>
      ) : fixDraft !== null ? (
        <div className="contribute-fix-form">
          <label className="contribute-field">
            <span>{t('contribute.fix_label')}</span>
            <input
              autoFocus
              value={fixDraft}
              onChange={(e) => setFixDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  applyFix();
                } else if (e.key === 'Escape') {
                  setFixDraft(null);
                }
              }}
            />
          </label>
          <p className="contribute-hint">{t('contribute.fix_hint')}</p>
          <div className="contribute-fix-actions">
            <button type="button" className="btn btn-accent" onClick={applyFix}>
              {t('contribute.fix_apply')}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setFixDraft(null)}>
              {t('contribute.fix_cancel')}
            </button>
          </div>
        </div>
      ) : (
        <p className="contribute-fix-open">
          {suggestion?.standard_spelling && (
            <span className="contribute-ai-note">
              ✨ {t('contribute.fix_ai_hint', { word: suggestion.standard_spelling })}{' '}
              <button
                type="button"
                className="contribute-link-btn"
                onClick={() => setFixDraft(suggestion.standard_spelling)}
              >
                {t('contribute.fix_ai_apply')}
              </button>
              {' · '}
            </span>
          )}
          <button
            type="button"
            className="contribute-link-btn"
            onClick={() => setFixDraft(task.token)}
          >
            {t('contribute.fix_open')}
          </button>
        </p>
      )}

      {task.occurrences > 1 && (
        <p className="contribute-meta">
          {t('contribute.define_occurrences', { count: task.occurrences })}
        </p>
      )}

      {knownFix ? (
        <p className="contribute-hint">{t('contribute.fix_known', { word: corrected })}</p>
      ) : (
        <>
          {suggestion?.explanation && (
            <p className="contribute-ai-note">✨ {suggestion.explanation}</p>
          )}
          {glossLanguage && (
            <label className="contribute-field">
              <span>
                {t('contribute.define_gloss_label', {
                  language: languageDisplayName(glossLanguage),
                })}
                {gloss.fromAi && <AiBadge />}
              </span>
              <input
                autoFocus={fixDraft === null}
                value={gloss.value}
                onChange={(e) => gloss.set(e.target.value)}
                placeholder={t('contribute.define_gloss_placeholder')}
              />
            </label>
          )}
          <div className="contribute-field-row">
            <label className="contribute-field">
              <span>
                {t('contribute.define_lemma_label')}
                {lemma.fromAi && <AiBadge />}
              </span>
              <input value={lemma.value} onChange={(e) => lemma.set(e.target.value)} />
            </label>
            <label className="contribute-field">
              <span>
                {t('contribute.define_pos_label')}
                {pos.fromAi && <AiBadge />}
              </span>
              <select value={pos.value} onChange={(e) => pos.set(e.target.value)}>
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
        </>
      )}
      <button type="submit" className="btn btn-accent" disabled={!ready || busy || fixDraft !== null}>
        {knownFix
          ? t('contribute.fix_save')
          : canEdit
            ? t('contribute.define_add')
            : t('contribute.define_suggest')}
      </button>
    </form>
  );
}

interface RecordAudioCardProps {
  task: RecordAudioTask;
  outbox: NonNullable<OutboxConfig['outbox']>;
  onError: (message: string) => void;
  onDone: () => void;
}

function RecordAudioCard({ task, outbox, onError, onDone }: RecordAudioCardProps) {
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
      <AudioRecorder
        wordFormId={task.word_form_id}
        canEdit
        outbox={outbox}
        onChange={handleChange}
        onQueued={() => setRecorded(true)}
        onError={onError}
      />
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

interface ConfirmSpellingCardProps {
  task: ConfirmSpellingTask;
  languageId: string;
  glossLanguage?: Language;
  busy: boolean;
  onSubmit: (data: SpellingAnswer) => void;
}

function ConfirmSpellingCard({
  task,
  languageId,
  glossLanguage,
  busy,
  onSubmit,
}: ConfirmSpellingCardProps) {
  const { t } = useTranslation();
  const suggestion = useWordSuggestion(languageId, {
    token: task.token,
    snippet_id: task.source.snippet_id,
    gloss_language_id: glossLanguage?.id,
  });
  const standardField = useSuggestedField(task.token, suggestion?.standard_spelling);
  const glossField = useSuggestedField('', suggestion?.gloss);
  const standard = standardField.value;
  const gloss = glossField.value;

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!standard.trim() || busy) return;
    onSubmit({
      token: task.token,
      standard: standard.trim(),
      snippet_id: task.source.snippet_id,
      gloss: gloss.trim() || undefined,
      gloss_language_id: gloss.trim() ? glossLanguage?.id : undefined,
    });
  };

  return (
    <form className="contribute-define" onSubmit={submit}>
      <p className="contribute-question">
        {t('contribute.spelling_question', { word: task.token })}
      </p>
      <OutsideSnippet source={task.source} />
      {task.occurrences > 1 && (
        <p className="contribute-meta">
          {t('contribute.spelling_occurrences', { count: task.occurrences })}
        </p>
      )}
      <label className="contribute-field">
        <span>
          {t('contribute.spelling_standard_label')}
          {standardField.fromAi && <AiBadge />}
        </span>
        <input autoFocus value={standard} onChange={(e) => standardField.set(e.target.value)} />
      </label>
      <p className="contribute-hint">{t('contribute.spelling_hint')}</p>
      {suggestion?.explanation && <p className="contribute-ai-note">✨ {suggestion.explanation}</p>}
      {glossLanguage && (
        <label className="contribute-field">
          <span>
            {t('contribute.spelling_gloss_label', {
              language: languageDisplayName(glossLanguage),
            })}
            {glossField.fromAi && <AiBadge />}
          </span>
          <input
            value={gloss}
            onChange={(e) => glossField.set(e.target.value)}
            placeholder={t('contribute.define_gloss_placeholder')}
          />
        </label>
      )}
      <button type="submit" className="btn btn-accent" disabled={!standard.trim() || busy}>
        {t('contribute.spelling_submit')}
      </button>
    </form>
  );
}

interface TranslateCardProps<T, A> {
  task: T;
  languages: Language[];
  targetLanguage: Language;
  busy: boolean;
  onSubmit: (data: A) => void;
}

function TranslateWordCard({
  task,
  languages,
  targetLanguage,
  busy,
  onSubmit,
}: TranslateCardProps<TranslateWordTask, TranslateWordAnswer>) {
  const { t } = useTranslation();
  const [lemma, setLemma] = useState('');
  const [pos, setPos] = useState(task.part_of_speech ?? '');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!lemma.trim() || busy) return;
    onSubmit({
      source_lexeme_id: task.source_lexeme_id,
      lemma: lemma.trim(),
      part_of_speech: pos || undefined,
    });
  };

  const others = task.translations.map(
    (tr) => `${tr.lemma} (${languageName(languages, tr.language_id) || tr.language_name || ''})`,
  );

  return (
    <form className="contribute-define" onSubmit={submit}>
      <p className="contribute-question">
        {t('contribute.translate_word_question', {
          word: task.lemma,
          language: languageDisplayName(targetLanguage),
        })}
      </p>
      <div className="contribute-word">{task.lemma}</div>
      <p className="contribute-meta">
        {languageName(languages, task.source_language_id)}
        {task.part_of_speech && ` · ${t(`add_word.pos_${task.part_of_speech}`)}`}
      </p>
      {others.length > 0 && (
        <p className="contribute-meta">{t('contribute.translate_also', { list: others.join(', ') })}</p>
      )}
      <div className="contribute-field-row">
        <label className="contribute-field">
          <span>{languageDisplayName(targetLanguage)}</span>
          <input autoFocus value={lemma} onChange={(e) => setLemma(e.target.value)} />
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
      <button type="submit" className="btn btn-accent" disabled={!lemma.trim() || busy}>
        {t('contribute.translate_submit')}
      </button>
    </form>
  );
}

function TranslateTextCard({
  task,
  languages,
  targetLanguage,
  busy,
  onSubmit,
}: TranslateCardProps<TranslateTextTask, TranslateTextAnswer>) {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!content.trim() || busy) return;
    onSubmit({
      text_id: task.text_id ?? undefined,
      snippet_id: task.snippet_id ?? undefined,
      title: title.trim() || undefined,
      content: content.trim(),
    });
  };

  return (
    <form className="contribute-define" onSubmit={submit}>
      <p className="contribute-question">
        {t('contribute.translate_text_question', {
          from: languageName(languages, task.source_language_id),
          language: languageDisplayName(targetLanguage),
        })}
      </p>
      <figure className="contribute-snippet contribute-source-text">
        <blockquote>{task.content}</blockquote>
        <figcaption>
          {task.source_url ? (
            <SourceCredit url={task.source_url} title={task.title} license={task.license} />
          ) : task.document_id ? (
            <Link to={`/documents/${task.document_id}`}>{task.title}</Link>
          ) : (
            task.title
          )}
        </figcaption>
      </figure>
      <label className="contribute-field">
        <span>{t('contribute.translate_text_label', { language: languageDisplayName(targetLanguage) })}</span>
        <textarea
          autoFocus
          rows={Math.min(8, Math.max(3, Math.ceil(task.content.length / 70)))}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </label>
      <label className="contribute-field">
        <span>{t('contribute.translate_title_label')}</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={task.title} />
      </label>
      <button type="submit" className="btn btn-accent" disabled={!content.trim() || busy}>
        {t('contribute.translate_submit')}
      </button>
    </form>
  );
}

/** Note text with its URL (if any) made clickable. */
function LinkedNote({ note }: { note: string }) {
  const match = note.match(/https?:\/\/\S+/);
  if (!match || match.index === undefined) return <>{note}</>;
  return (
    <>
      {note.slice(0, match.index)}
      <a href={match[0]} target="_blank" rel="noopener noreferrer">
        {match[0]}
      </a>
      {note.slice(match.index + match[0].length)}
    </>
  );
}

function ReviewAdditionCard({ task, languages }: { task: ReviewAdditionTask; languages: Language[] }) {
  const { t } = useTranslation();
  return (
    <div className="contribute-review">
      {task.proposal_type === 'add_spelling_variant' ? (
        <>
          <p className="contribute-question">
            {t('contribute.review_spelling_question', { variant: task.variant, lemma: task.lemma })}
          </p>
          <div className="contribute-word">
            {task.variant} → <Link to={`/words/${task.lexeme_id}`}>{task.lemma}</Link>
          </div>
          {task.note && (
            <p className="contribute-meta">
              <LinkedNote note={task.note} />
            </p>
          )}
          {task.fix_texts && <p className="contribute-meta">{t('contribute.review_fix_texts')}</p>}
        </>
      ) : (
        <>
          <p className="contribute-question">
            {t('contribute.review_translation_question', {
              lemma: task.lemma,
              other: task.other_lemma,
              language: languageName(languages, task.other_language_id),
            })}
          </p>
          <div className="contribute-word">
            <Link to={`/words/${task.lexeme_id}`}>{task.lemma}</Link> = {task.other_lemma}
          </div>
        </>
      )}
      {task.creator_username && (
        <p className="contribute-meta">
          {t('review.suggested_by', { username: task.creator_username })}
        </p>
      )}
    </div>
  );
}
