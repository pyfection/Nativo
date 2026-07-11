import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';

import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import { fullAudioUrl, listAudioForForm } from '../services/audioService';
import learnService, {
  LearningPathEntry,
  PlacementLevel,
  ReviewCard,
} from '../services/learnService';
import './Learn.css';
import { languageDisplayName } from '../utils/languageName';

interface LearnProps {
  selectedLanguage: Language;
}

const RATING_LABEL: Record<string, string> = {
  easy: '😀',
  just_right: '🙂',
  challenging: '😅',
  too_hard: '😮‍💨',
};

/**
 * The learner's line through the corpus: completed texts, the recommended
 * next one, and what's coming up. Nothing is hard-locked — later texts are
 * visible with an honest "this will be tough" signal instead.
 */
export default function Learn({ selectedLanguage }: LearnProps) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [path, setPath] = useState<LearningPathEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Practice deck (shaky words) + placement card state.
  const [deck, setDeck] = useState<ReviewCard[]>([]);
  const [knowledgeCount, setKnowledgeCount] = useState<number | null>(null);
  const [practicing, setPracticing] = useState(false);
  const [cardIndex, setCardIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [knewCount, setKnewCount] = useState(0);
  const [cardAudioUrl, setCardAudioUrl] = useState<string | null>(null);
  const [placementBusy, setPlacementBusy] = useState(false);
  const [placementMessage, setPlacementMessage] = useState('');
  const [placementDismissed, setPlacementDismissed] = useState(false);

  const placementStorageKey = `nativo-placement-${selectedLanguage.id}`;

  const fetchPath = useCallback(() => {
    return learnService.getPath(selectedLanguage.id).then((entries) => setPath(entries));
  }, [selectedLanguage.id]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    learnService
      .getPath(selectedLanguage.id)
      .then((entries) => {
        if (!cancelled) setPath(entries);
      })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || t('learn.load_failed'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id, isAuthenticated, t]);

  // Deck + knowledge are personal; guests see neither.
  useEffect(() => {
    setDeck([]);
    setKnowledgeCount(null);
    setPracticing(false);
    setPlacementMessage('');
    setPlacementDismissed(window.localStorage.getItem(placementStorageKey) === '1');
    if (!isAuthenticated) return;
    let cancelled = false;
    Promise.all([
      learnService.getReviewDeck(selectedLanguage.id),
      learnService.getWordKnowledge(selectedLanguage.id),
    ])
      .then(([cards, knowledge]) => {
        if (cancelled) return;
        setDeck(cards);
        setKnowledgeCount(knowledge.length);
      })
      .catch(() => {
        // Practice is a bonus; the path still renders without it.
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, selectedLanguage.id, placementStorageKey]);

  // Fetch pronunciation audio when a card's answer is revealed.
  useEffect(() => {
    setCardAudioUrl(null);
    if (!practicing || !revealed) return;
    const card = deck[cardIndex];
    if (!card?.lemma_form_id) return;
    let cancelled = false;
    listAudioForForm(card.lemma_form_id)
      .then((rows) => {
        if (!cancelled && rows.length > 0) setCardAudioUrl(fullAudioUrl(rows[0].file_path));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [practicing, revealed, cardIndex, deck]);

  const startPractice = () => {
    setCardIndex(0);
    setRevealed(false);
    setKnewCount(0);
    setPracticing(true);
  };

  const answerCard = async (knew: boolean) => {
    const card = deck[cardIndex];
    if (!card) return;
    if (knew) setKnewCount((n) => n + 1);
    try {
      await learnService.reviewWord(card.lexeme_id, knew);
    } catch {
      // Scoring is best-effort; keep the flow moving.
    }
    setRevealed(false);
    setCardIndex((i) => i + 1);
  };

  const finishPractice = () => {
    setPracticing(false);
    learnService
      .getReviewDeck(selectedLanguage.id)
      .then(setDeck)
      .catch(() => {});
    void fetchPath();
  };

  const choosePlacement = async (level: PlacementLevel) => {
    window.localStorage.setItem(placementStorageKey, '1');
    setPlacementDismissed(true);
    if (level === 'beginner') return;
    setPlacementBusy(true);
    try {
      const seeded = await learnService.applyPlacement(selectedLanguage.id, level);
      setPlacementMessage(
        seeded > 0 ? t('learn.placement_done', { n: seeded }) : t('learn.placement_done_zero'),
      );
      setKnowledgeCount((n) => (n ?? 0) + seeded);
      await fetchPath();
    } catch (err: any) {
      setPlacementMessage(err.response?.data?.detail || t('learn.load_failed'));
    } finally {
      setPlacementBusy(false);
    }
  };

  const completedCount = path.filter((e) => e.state === 'completed').length;
  const showPlacement =
    isAuthenticated && !placementDismissed && knowledgeCount === 0 && path.length > 0;
  const currentCard = practicing ? deck[cardIndex] : undefined;
  const roundOver = practicing && cardIndex >= deck.length;

  return (
    <div className="learn-page">
      <div className="learn-header">
        <h1>{t('learn.heading', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="learn-subtitle">{t('learn.subtitle')}</p>
      </div>

      {!isAuthenticated && (
        <div className="learn-guest-banner">
          {t('learn.guest_banner')}{' '}
          <Link to="/register" state={{ from: location }}>
            {t('learn.guest_banner_cta')}
          </Link>
        </div>
      )}

      {loading && <div className="loading-state">{t('learn.loading')}</div>}
      {error && <div className="error-state">{error}</div>}

      {showPlacement && (
        <div className="learn-placement-card">
          <h2>{t('learn.placement_title', { language: languageDisplayName(selectedLanguage) })}</h2>
          <p>{t('learn.placement_subtitle')}</p>
          <div className="learn-placement-options">
            <button
              type="button"
              className="btn-secondary"
              disabled={placementBusy}
              onClick={() => void choosePlacement('beginner')}
            >
              {t('learn.placement_beginner')}
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={placementBusy}
              onClick={() => void choosePlacement('intermediate')}
            >
              {t('learn.placement_intermediate')}
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={placementBusy}
              onClick={() => void choosePlacement('advanced')}
            >
              {t('learn.placement_advanced')}
            </button>
          </div>
        </div>
      )}
      {placementMessage && <div className="learn-placement-message">{placementMessage}</div>}

      {isAuthenticated && !practicing && deck.length > 0 && (
        <div className="learn-practice-card">
          <div>
            <h2>{t('learn.practice_title')}</h2>
            <p>
              {deck.length === 1
                ? t('learn.practice_intro_one')
                : t('learn.practice_intro', { n: deck.length })}
            </p>
          </div>
          <button type="button" className="btn-primary" onClick={startPractice}>
            {t('learn.practice_start')}
          </button>
        </div>
      )}

      {practicing && !roundOver && currentCard && (
        <div className="learn-flashcard">
          <div className="learn-flashcard-progress">
            {t('learn.practice_progress', { current: cardIndex + 1, total: deck.length })}
          </div>
          <div className="learn-flashcard-word" lang={selectedLanguage.iso || undefined}>
            {currentCard.lemma}
          </div>
          {!revealed ? (
            <button type="button" className="btn-primary" onClick={() => setRevealed(true)}>
              {t('learn.practice_show')}
            </button>
          ) : (
            <>
              <div className="learn-flashcard-answer">
                {currentCard.ipa_pronunciation && (
                  <div className="learn-flashcard-ipa">/{currentCard.ipa_pronunciation}/</div>
                )}
                {currentCard.translations.length > 0 ? (
                  <ul className="learn-flashcard-translations">
                    {currentCard.translations.map((tr) => (
                      <li key={`${tr.language_id}-${tr.lemma}`}>{tr.lemma}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="learn-flashcard-none">{t('learn.practice_no_translations')}</p>
                )}
                {cardAudioUrl && (
                  <audio controls preload="metadata" src={cardAudioUrl} className="learn-flashcard-audio" />
                )}
              </div>
              <div className="learn-flashcard-verdicts">
                <button type="button" className="btn-knew" onClick={() => void answerCard(true)}>
                  {t('learn.practice_knew')}
                </button>
                <button type="button" className="btn-missed" onClick={() => void answerCard(false)}>
                  {t('learn.practice_missed')}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {roundOver && (
        <div className="learn-flashcard learn-flashcard-summary">
          <h2>{t('learn.practice_done_title')}</h2>
          <p>{t('learn.practice_done', { knew: knewCount, total: deck.length })}</p>
          <button type="button" className="btn-primary" onClick={finishPractice}>
            {t('learn.practice_finish')}
          </button>
        </div>
      )}

      {!loading && !error && path.length === 0 && (
        <div className="learn-empty">
          <p>{t('learn.empty', { language: languageDisplayName(selectedLanguage) })}</p>
          <p className="learn-empty-hint">{t('learn.empty_hint')}</p>
        </div>
      )}

      {!loading && path.length > 0 && (
        <>
          {isAuthenticated && completedCount > 0 && (
            <p className="learn-progress-line">
              {t('learn.progress', { done: completedCount, total: path.length })}
            </p>
          )}
          <ol className="learn-track">
            {path.map((entry) => (
              <li key={entry.text_id} className={`learn-step learn-step-${entry.state}`}>
                <span className="learn-step-marker" aria-hidden="true">
                  {entry.state === 'completed'
                    ? '✓'
                    : entry.state === 'recommended'
                      ? '▶'
                      : '·'}
                </span>
                <Link to={`/learn/${entry.document_id}`} className="learn-step-card">
                  <span className="learn-step-title">{entry.title}</span>
                  <span className="learn-step-meta">
                    {entry.state === 'completed' ? (
                      <>
                        {t('learn.step_completed')}
                        {entry.difficulty_rating && (
                          <span className="learn-step-rating" title={entry.difficulty_rating}>
                            {RATING_LABEL[entry.difficulty_rating]}
                          </span>
                        )}
                      </>
                    ) : (
                      <>
                        {entry.new_lexeme_count === 0
                          ? t('learn.step_no_new_words')
                          : entry.new_lexeme_count === 1
                            ? t('learn.step_new_word_one')
                            : t('learn.step_new_words', { n: entry.new_lexeme_count })}
                        {isAuthenticated && entry.total_lexemes > 0 && (
                          <> · {t('learn.step_known', { pct: entry.known_pct })}</>
                        )}
                      </>
                    )}
                  </span>
                  {entry.state === 'recommended' && (
                    <span className="learn-step-go">{t('learn.step_start')} →</span>
                  )}
                  {entry.state === 'upcoming' &&
                    isAuthenticated &&
                    entry.known_pct < 80 &&
                    entry.total_lexemes > 0 && (
                      <span className="learn-step-warning">{t('learn.step_tough')}</span>
                    )}
                </Link>
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
