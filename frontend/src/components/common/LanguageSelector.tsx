import { useState } from 'react';
import { Language } from '../../App';
import { useAuth } from '../../contexts/AuthContext';
import JoinLanguageModal from './JoinLanguageModal';
import './LanguageSelector.css';

interface LanguageSelectorProps {
  languages: Language[];
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  onLanguageJoined?: () => void;
}

export default function LanguageSelector({ 
  languages, 
  selectedLanguage, 
  onLanguageChange,
  onLanguageJoined 
}: LanguageSelectorProps) {
  const { user, isAuthenticated } = useAuth();
  const [showJoinModal, setShowJoinModal] = useState(false);

  // Check if user is a member of the selected language
  const userProficiency = user?.language_proficiencies?.find(
    (lp) => lp.language_id === selectedLanguage.id
  );

  const handleJoinClick = () => {
    if (!isAuthenticated) {
      // Could redirect to login or show a message
      alert('Please log in to join a language');
      return;
    }
    setShowJoinModal(true);
  };

  const handleJoined = async () => {
    // Refresh user proficiencies after joining
    if (onLanguageJoined) {
      await onLanguageJoined();
    }
  };

  return (
    <>
      <div className="language-selector">
        <label htmlFor="language-select" className="selector-label">
          Language:
        </label>
        <select
          id="language-select"
          value={selectedLanguage.id}
          onChange={(e) => {
            const language = languages.find(lang => lang.id === e.target.value);
            if (language) {
              onLanguageChange(language);
            }
          }}
          className="selector-dropdown"
        >
          {languages.map((language) => (
            <option key={language.id} value={language.id}>
              {language.name} ({language.nativeName})
            </option>
          ))}
        </select>

        {isAuthenticated && (
          <>
            {!userProficiency ? (
              <button
                onClick={handleJoinClick}
                className="join-button"
                title="Join this language"
              >
                Join
              </button>
            ) : (
              <div className="proficiency-badge" title={`Proficiency: ${userProficiency.proficiency_level}`}>
                <span className="proficiency-level">
                  {userProficiency.proficiency_level.charAt(0).toUpperCase() + userProficiency.proficiency_level.slice(1)}
                </span>
                {(userProficiency.can_edit || userProficiency.can_verify) && (
                  <span className="permission-icons">
                    {userProficiency.can_edit && (
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" title="Can edit">
                        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                      </svg>
                    )}
                    {userProficiency.can_verify && (
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" title="Can verify">
                        <path d="M10.067.87a2.89 2.89 0 0 0-4.134 0l-.622.638-.89-.011a2.89 2.89 0 0 0-2.924 2.924l.01.89-.636.622a2.89 2.89 0 0 0 0 4.134l.637.622-.011.89a2.89 2.89 0 0 0 2.924 2.924l.89-.01.622.636a2.89 2.89 0 0 0 4.134 0l.622-.637.89.011a2.89 2.89 0 0 0 2.924-2.924l-.01-.89.636-.622a2.89 2.89 0 0 0 0-4.134l-.637-.622.011-.89a2.89 2.89 0 0 0-2.924-2.924l-.89.01-.622-.636zm.287 5.984-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7 8.793l2.646-2.647a.5.5 0 0 1 .708.708z"/>
                      </svg>
                    )}
                  </span>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <JoinLanguageModal
        isOpen={showJoinModal}
        onClose={() => setShowJoinModal(false)}
        language={selectedLanguage}
        onJoined={handleJoined}
      />
    </>
  );
}

