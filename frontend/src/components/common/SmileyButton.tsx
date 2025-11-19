import { useState, useEffect } from 'react';
import './SmileyButton.css';

/**
 * SmileyButton component that displays a smiley emoji button.
 * When clicked, shows "You are awesome!" message for 5 seconds.
 */
export default function SmileyButton() {
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (showMessage) {
      const timer = setTimeout(() => {
        setShowMessage(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [showMessage]);

  const handleClick = () => {
    setShowMessage(true);
  };

  return (
    <div className="smiley-button-container">
      <button 
        className="smiley-button" 
        onClick={handleClick}
        aria-label="Show awesome message"
      >
        😊
      </button>
      {showMessage && (
        <div className="smiley-message">
          You are awesome!
        </div>
      )}
    </div>
  );
}
