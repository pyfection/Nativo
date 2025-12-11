import { useState, useEffect } from 'react';
import './SmileyButton.css';

/**
 * SmileyButton component that displays a smiley emoji button.
 * When clicked, shows a popup modal with an encouraging message.
 */
export default function SmileyButton() {
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const handleClick = () => {
    setIsPopupOpen(true);
  };

  const handleClose = () => {
    setIsPopupOpen(false);
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    if (isPopupOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isPopupOpen]);

  return (
    <>
      <button 
        className="smiley-button" 
        onClick={handleClick}
        aria-label="Show awesome message"
        type="button"
      >
        😊
      </button>
      {isPopupOpen && (
        <div className="smiley-popup-overlay" onClick={handleClose}>
          <div className="smiley-popup-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="smiley-popup-close" 
              onClick={handleClose}
              aria-label="Close"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
            <div className="smiley-popup-body">
              <div className="smiley-emoji">😊</div>
              <p className="smiley-message">You are awesomest!</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
