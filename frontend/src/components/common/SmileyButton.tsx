import { useState } from 'react';
import Modal from './Modal';
import './SmileyButton.css';

export default function SmileyButton() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        className="smiley-button"
        onClick={() => setIsModalOpen(true)}
        aria-label="Show awesome message"
      >
        😊
      </button>
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      >
        <div className="smiley-modal-content">
          <div className="smiley-modal-emoji">😊</div>
          <p className="smiley-modal-message">You are awesomest!</p>
        </div>
      </Modal>
    </>
  );
}
