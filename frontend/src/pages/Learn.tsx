import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';

import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import learnService, { LearningPathEntry } from '../services/learnService';
import './Learn.css';

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
  }, [selectedLanguage.id, isAuthenticated]);

  const completedCount = path.filter((e) => e.state === 'completed').length;

  return (
    <div className="learn-page">
      <div className="learn-header">
        <h1>{t('learn.heading', { language: selectedLanguage.name })}</h1>
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

      {!loading && !error && path.length === 0 && (
        <div className="learn-empty">
          <p>{t('learn.empty', { language: selectedLanguage.name })}</p>
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
