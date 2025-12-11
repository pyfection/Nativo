import { useState } from 'react';
import Modal from './Modal';
import './SmileyButton.css';

/**
 * SmileyButton component that displays a smiley button in the header.
 * When clicked, shows a popup with an encouraging message.
 */
export default function SmileyButton() {
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const handleClick = () => {
    setIsPopupOpen(true);
  };

  const handleClose = () => {
    setIsPopupOpen(false);
  };

  return (
    <>
      <button 
        className="smiley-button" 
        onClick={handleClick}
        aria-label="Show awesome message"
        title="You are awesome!"
      >
        😊
      </button>
      <Modal 
        isOpen={isPopupOpen} 
        onClose={handleClose}
        title=""
      >
        <div className="smiley-popup-content">
          <div className="smiley-popup-emoji">😊</div>
          <p className="smiley-popup-message">You are awesomest!</p>
        </div>
      </Modal>
    </>
  );
}
