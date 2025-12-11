import { useState } from 'react';
import Modal from './Modal';
import './SmileyButton.css';

/**
 * SmileyButton component that displays a smiley emoji button
 * and shows a popup message when clicked.
 */
export default function SmileyButton() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleClick = () => {
    setIsModalOpen(true);
  };

  const handleClose = () => {
    setIsModalOpen(false);
  };

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
      <Modal 
        isOpen={isModalOpen} 
        onClose={handleClose}
        title="Awesome!"
      >
        <p className="smiley-message">You are awesomest!</p>
      </Modal>
    </>
  );
}
