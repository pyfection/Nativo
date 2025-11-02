import { useState } from 'react';
import Modal from './Modal';
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
    label: 'Native Speaker',
    description: 'This is your first language or you speak it at a native level',
  },
  {
    value: 'fluent' as const,
    label: 'Fluent',
    description: 'You can speak, read, and write fluently with minimal errors',
  },
  {
    value: 'intermediate' as const,
    label: 'Intermediate',
    description: 'You have a good working knowledge but still learning',
  },
  {
    value: 'beginner' as const,
    label: 'Beginner',
    description: 'You are just starting to learn this language',
  },
];

export default function JoinLanguageModal({ isOpen, onClose, language, onJoined }: JoinLanguageModalProps) {
  const { user } = useAuth();
  const [selectedProficiency, setSelectedProficiency] = useState<ProficiencyLevel>('beginner');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setError('You must be logged in to join a language');
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
      setError(err.response?.data?.detail || 'Failed to join language');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Join ${language.name}`}>
      <form onSubmit={handleSubmit} className="join-language-form">
        <p className="join-language-intro">
          Select your proficiency level in <strong>{language.name}</strong> ({language.nativeName}).
          This helps others understand your expertise.
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
                <div className="proficiency-label">{level.label}</div>
                <div className="proficiency-description">{level.description}</div>
              </div>
            </label>
          ))}
        </div>

        <div className="join-language-note">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zM7.5 4.5v2h1v-2h-1zm0 3v5h1v-5h-1z"/>
          </svg>
          <span>Permissions to edit and verify content are granted by administrators.</span>
        </div>

        {error && (
          <div className="join-language-error">
            {error}
          </div>
        )}

        <div className="join-language-actions">
          <button type="button" onClick={onClose} className="btn-secondary" disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Joining...' : 'Join Language'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

