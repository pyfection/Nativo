import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import documentService, { TextSuggestion } from '../services/documentService';
import wordService, { LexemeSuggestion } from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
import './Review.css';

interface ReviewProps {
  selectedLanguage: Language;
}

/**
 * The reviewer's queue: word and text suggestions from non-editors awaiting
 * a verdict. Approve publishes (and, for words, can auto-promote a trusted
 * suggester to editor); reject archives with an optional reason.
 */
export default function Review({ selectedLanguage }: ReviewProps) {
  const { t } = useTranslation();
  const { canVerifyLanguage } = useAuth();
  const [words, setWords] = useState<LexemeSuggestion[]>([]);
  const [texts, setTexts] = useState<TextSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);

  const canVerify = canVerifyLanguage(selectedLanguage.id);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const [wordData, textData] = await Promise.all([
        wordService.listSuggestions(selectedLanguage.id),
        documentService.listSuggestions(selectedLanguage.id),
      ]);
      setWords(wordData);
      setTexts(textData);
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

  const promptReason = () =>
    window.prompt(t('review.reject_reason_prompt')) || undefined;

  const actOnWord = async (id: string, action: 'approve' | 'reject') => {
    const reason = action === 'reject' ? promptReason() : undefined;
    try {
      setBusyId(id);
      if (action === 'approve') await wordService.verify(id);
      else await wordService.reject(id, reason);
      setWords((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      setError(err.response?.data?.detail || t('review.action_failed'));
    } finally {
      setBusyId(null);
    }
  };

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

  const empty = !loading && words.length === 0 && texts.length === 0;

  return (
    <div className="review-page">
      <div className="review-header">
        <h1>{t('review.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="review-subtitle">{t('review.subtitle')}</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {loading && <div className="loading-state">{t('review.loading')}</div>}

      {empty && <div className="review-empty">{t('review.empty')}</div>}

      {words.length > 0 && (
        <section className="review-section">
          <h2 className="review-section-title">{t('review.words_heading')}</h2>
          <ul className="review-list">
            {words.map((item) => (
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
                {actions(item.id, (action) => void actOnWord(item.id, action))}
              </li>
            ))}
          </ul>
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
