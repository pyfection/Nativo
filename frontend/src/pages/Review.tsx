import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import wordService, { LexemeSuggestion } from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
import './Review.css';

interface ReviewProps {
  selectedLanguage: Language;
}

/**
 * The reviewer's queue: word suggestions from non-editors awaiting a
 * verdict. Approve publishes (and can auto-promote a trusted suggester to
 * editor); reject archives with an optional reason.
 */
export default function Review({ selectedLanguage }: ReviewProps) {
  const { t } = useTranslation();
  const { canVerifyLanguage } = useAuth();
  const [items, setItems] = useState<LexemeSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  const canVerify = canVerifyLanguage(selectedLanguage.id);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await wordService.listSuggestions(selectedLanguage.id);
      setItems(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.load_failed'));
    } finally {
      setLoading(false);
    }
  }, [selectedLanguage.id, t]);

  useEffect(() => {
    if (canVerify) void refresh();
  }, [canVerify, refresh]);

  if (!canVerify) {
    return (
      <div className="review-page">
        <h1>{t('review.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="review-no-permission">{t('review.no_permission')}</p>
      </div>
    );
  }

  const act = async (id: string, action: 'approve' | 'reject') => {
    let reason: string | undefined;
    if (action === 'reject') {
      reason = window.prompt(t('review.reject_reason_prompt')) || undefined;
    }
    try {
      setBusyId(id);
      if (action === 'approve') await wordService.verify(id);
      else await wordService.reject(id, reason);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.action_failed'));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="review-page">
      <div className="review-header">
        <h1>{t('review.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="review-subtitle">{t('review.subtitle')}</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {loading && <div className="loading-state">{t('review.loading')}</div>}

      {!loading && items.length === 0 && (
        <div className="review-empty">{t('review.empty')}</div>
      )}

      {items.length > 0 && (
        <ul className="review-list">
          {items.map((item) => (
            <li key={item.id} className="review-item">
              <div className="review-item-main">
                <Link to={`/words/${item.id}`} className="review-item-lemma">
                  {item.lemma}
                </Link>
                {item.part_of_speech && (
                  <span className="review-item-pos">{item.part_of_speech}</span>
                )}
                {item.forms.filter((f) => !f.is_lemma).length > 0 && (
                  <span className="review-item-forms">
                    {item.forms.filter((f) => !f.is_lemma).map((f) => f.form).join(', ')}
                  </span>
                )}
              </div>
              <div className="review-item-meta">
                {item.creator_username && (
                  <span>{t('review.suggested_by', { username: item.creator_username })}</span>
                )}
              </div>
              <div className="review-item-actions">
                <button
                  type="button"
                  className="btn-approve"
                  disabled={busyId === item.id}
                  onClick={() => void act(item.id, 'approve')}
                >
                  {t('review.approve')}
                </button>
                <button
                  type="button"
                  className="btn-reject"
                  disabled={busyId === item.id}
                  onClick={() => void act(item.id, 'reject')}
                >
                  {t('review.reject')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
