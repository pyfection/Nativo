import { useState } from 'react';
import { LanguageResponse } from '../../services/languageService';
import { useAuth } from '../../contexts/AuthContext';
import JoinLanguageModal from '../common/JoinLanguageModal';
import { Language } from '../../App';
import './LanguageCard.css';

interface LanguageCardProps {
  language: LanguageResponse;
  onLanguageJoined?: () => void;
}

export default function LanguageCard({ language, onLanguageJoined }: LanguageCardProps) {
  const { user } = useAuth();
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const userProficiency = user?.language_proficiencies?.find(
    (lp) => lp.language_id === language.id
  );

  // Convert LanguageResponse to Language for the modal
  const languageForModal: Language = {
    id: language.id,
    name: language.name,
    nativeName: language.native_name || language.name,
    iso: language.iso_639_3 || '',
    description: language.description || '',
    colorScheme: {
      primary: language.primary_color || '#8B4513',
      secondary: language.secondary_color || '#D2691E',
      accent: language.accent_color || '#CD853F',
      background: language.background_color || '#FFF8DC',
    },
  };

  const handleJoined = async () => {
    if (onLanguageJoined) {
      await onLanguageJoined();
    }
    setShowJoinModal(false);
  };

  return (
    <>
      <div 
        className="language-card"
        style={{
          borderLeftColor: language.primary_color || '#8B4513',
        }}
      >
        <div className="language-card-header">
          <div>
            <h3 className="language-name">{language.name}</h3>
            {language.native_name && language.native_name !== language.name && (
              <p className="language-native-name">{language.native_name}</p>
            )}
            {language.iso_639_3 && (
              <span className="language-iso">ISO: {language.iso_639_3}</span>
            )}
          </div>

          {language.is_endangered && (
            <span className="endangered-badge" title="Endangered language">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
              </svg>
              Endangered
            </span>
          )}
        </div>

        {language.description && (
          <p className={`language-description ${expanded ? 'expanded' : ''}`}>
            {language.description}
          </p>
        )}

        {language.description && language.description.length > 150 && (
          <button
            className="expand-button"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}

        {/* User proficiency if joined */}
        {userProficiency && (
          <div className="language-membership">
            <div className="proficiency-info">
              <span className="proficiency-label">Your proficiency:</span>
              <span className="proficiency-value">
                {userProficiency.proficiency_level.charAt(0).toUpperCase() + 
                 userProficiency.proficiency_level.slice(1)}
              </span>
            </div>
            {(userProficiency.can_edit || userProficiency.can_verify) && (
              <div className="permissions-info">
                {userProficiency.can_edit && (
                  <span className="permission-badge edit">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                    Can Edit
                  </span>
                )}
                {userProficiency.can_verify && (
                  <span className="permission-badge verify">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M10.067.87a2.89 2.89 0 0 0-4.134 0l-.622.638-.89-.011a2.89 2.89 0 0 0-2.924 2.924l.01.89-.636.622a2.89 2.89 0 0 0 0 4.134l.637.622-.011.89a2.89 2.89 0 0 0 2.924 2.924l.89-.01.622.636a2.89 2.89 0 0 0 4.134 0l.622-.637.89.011a2.89 2.89 0 0 0 2.924-2.924l-.01-.89.636-.622a2.89 2.89 0 0 0 0-4.134l-.637-.622.011-.89a2.89 2.89 0 0 0-2.924-2.924l-.89.01-.622-.636zm.287 5.984-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 1 1 .708-.708L7 8.793l2.646-2.647a.5.5 0 0 1 .708.708z"/>
                    </svg>
                    Can Verify
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Action button */}
        <div className="language-card-actions">
          {!userProficiency ? (
            <button
              className="btn-join"
              onClick={() => setShowJoinModal(true)}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
              </svg>
              Join Language
            </button>
          ) : (
            <button className="btn-manage" disabled title="Coming soon">
              Manage
            </button>
          )}
        </div>
      </div>

      <JoinLanguageModal
        isOpen={showJoinModal}
        onClose={() => setShowJoinModal(false)}
        language={languageForModal}
        onJoined={handleJoined}
      />
    </>
  );
}

