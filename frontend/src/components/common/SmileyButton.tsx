import { useState, useEffect } from 'react';
import './SmileyButton.css';

export default function SmileyButton() {
  const [showMessage, setShowMessage] = useState(false);

  const handleClick = () => {
    setShowMessage(true);
  };

  useEffect(() => {
    if (showMessage) {
      const timer = setTimeout(() => {
        setShowMessage(false);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [showMessage]);

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
