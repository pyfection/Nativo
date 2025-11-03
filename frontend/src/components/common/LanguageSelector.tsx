import { useState } from 'react';
import { Link } from 'react-router-dom';
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

  // Split languages into managed and other
  const managedLanguages = languages.filter(lang => lang.managed);
  const otherLanguages = languages.filter(lang => !lang.managed);

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
          {managedLanguages.length > 0 && (
            <>
              {managedLanguages.map((language) => (
                <option key={language.id} value={language.id}>
                  {language.name} ({language.nativeName})
                </option>
              ))}
              {otherLanguages.length > 0 && (
                <option disabled>────────────────</option>
              )}
            </>
          )}
          {otherLanguages.map((language) => (
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

        <Link
          to="/languages"
          className="languages-icon-button"
          title="Browse all languages"
        >
          <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4.545 6.714 4.11 8H3l1.862-5h1.284L8 8H6.833l-.435-1.286H4.545zm1.634-.736L5.5 3.956h-.049l-.679 2.022H6.18z"/>
            <path d="M0 2a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v3h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-3H2a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2zm7.138 9.995c.193.301.402.583.63.846-.748.575-1.673 1.001-2.768 1.292.178.217.451.635.555.867 1.125-.359 2.08-.844 2.886-1.494.777.665 1.739 1.165 2.93 1.472.133-.254.414-.673.629-.89-1.125-.253-2.057-.694-2.82-1.284.681-.747 1.222-1.651 1.621-2.757H14V8h-3v1.047h.765c-.318.844-.74 1.546-1.272 2.13a6.066 6.066 0 0 1-.415-.492 1.988 1.988 0 0 1-.94.31z"/>
          </svg>
        </Link>
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

