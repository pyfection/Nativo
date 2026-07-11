import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from './Modal';
import { languageDisplayName } from '../../utils/languageName';
import { Language } from '../../App';
import { useAuth } from '../../contexts/AuthContext';
import userLanguageService, { ProficiencyLevel } from '../../services/userLanguageService';
import './JoinLanguageModal.css';

interface JoinLanguageModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
  onJoined?: () => void;
}

const PROFICIENCY_LEVELS = [
  {
    value: 'native' as const,
    label: 'join_modal.native_label',
    description: 'join_modal.native_description',
  },
  {
    value: 'fluent' as const,
    label: 'join_modal.fluent_label',
    description: 'join_modal.fluent_description',
  },
  {
    value: 'intermediate' as const,
    label: 'join_modal.intermediate_label',
    description: 'join_modal.intermediate_description',
  },
  {
    value: 'beginner' as const,
    label: 'join_modal.beginner_label',
    description: 'join_modal.beginner_description',
  },
];

export default function JoinLanguageModal({ isOpen, onClose, language, onJoined }: JoinLanguageModalProps) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [selectedProficiency, setSelectedProficiency] = useState<ProficiencyLevel>('beginner');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setError(t('join_modal.must_be_logged_in'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      await userLanguageService.joinLanguage(user.id, {
        language_id: language.id,
        proficiency_level: selectedProficiency,
      });
      if (onJoined) {
        await onJoined();
      }
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || t('join_modal.join_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={t('join_modal.title', { language: languageDisplayName(language) })}>
      <form onSubmit={handleSubmit} className="join-language-form">
        <p className="join-language-intro">
          {t('join_modal.intro_pre')} <strong>{languageDisplayName(language)}</strong> ({language.nativeName}).{' '}
          {t('join_modal.intro_post')}
        </p>

        <div className="proficiency-options">
          {PROFICIENCY_LEVELS.map((level) => (
            <label key={level.value} className={`proficiency-option ${selectedProficiency === level.value ? 'selected' : ''}`}>
              <input
                type="radio"
                name="proficiency"
                value={level.value}
                checked={selectedProficiency === level.value}
                onChange={(e) => setSelectedProficiency(e.target.value as typeof selectedProficiency)}
                className="proficiency-radio"
              />
              <div className="proficiency-content">
                <div className="proficiency-label">{t(level.label)}</div>
                <div className="proficiency-description">{t(level.description)}</div>
              </div>
            </label>
          ))}
        </div>

        <div className="join-language-note">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM7.5 4.5v2h1v-2h-1zm0 3v5h1v-5h-1z"/>
          </svg>
          <span>{t('join_modal.permissions_note')}</span>
        </div>

        {error && (
          <div className="join-language-error">
            {error}
          </div>
        )}

        <div className="join-language-actions">
          <button type="button" onClick={onClose} className="btn-secondary" disabled={loading}>
            {t('join_modal.cancel')}
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? t('join_modal.joining') : t('join_modal.join_language')}
          </button>
        </div>
      </form>
    </Modal>
  );
}

