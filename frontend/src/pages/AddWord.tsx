import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Language } from '../App';
import wordService, { CreateWordData } from '../services/wordService';
import './AddWord.css';

interface AddWordProps {
  selectedLanguage: Language;
}

export default function AddWord({ selectedLanguage }: AddWordProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<CreateWordData>({
    word: '',
    language_id: selectedLanguage.id,
    definition: '',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
  }, [isAuthenticated, navigate]);

  // Update language_id when selectedLanguage changes
  useEffect(() => {
    setFormData(prev => ({ ...prev, language_id: selectedLanguage.id }));
  }, [selectedLanguage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await wordService.create(formData);
      navigate('/words');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create word');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="add-word-page">
      <div className="page-header">
        <h1>Add New Word</h1>
        <p>Adding word to: <strong>{selectedLanguage.name} ({selectedLanguage.nativeName})</strong></p>
      </div>

      <form onSubmit={handleSubmit} className="word-form">
        {error && <div className="error-message">{error}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="word">Word *</label>
            <input
              type="text"
              id="word"
              name="word"
              value={formData.word}
              onChange={handleChange}
              required
              placeholder="Enter the word"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="romanization">Romanization</label>
            <input
              type="text"
              id="romanization"
              name="romanization"
              value={formData.romanization || ''}
              onChange={handleChange}
              placeholder="Latin script transliteration"
            />
          </div>

          <div className="form-group">
            <label htmlFor="ipa_pronunciation">IPA Pronunciation</label>
            <input
              type="text"
              id="ipa_pronunciation"
              name="ipa_pronunciation"
              value={formData.ipa_pronunciation || ''}
              onChange={handleChange}
              placeholder="International Phonetic Alphabet"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="part_of_speech">Part of Speech</label>
            <select
              id="part_of_speech"
              name="part_of_speech"
              value={formData.part_of_speech || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              <option value="noun">Noun</option>
              <option value="verb">Verb</option>
              <option value="adjective">Adjective</option>
              <option value="adverb">Adverb</option>
              <option value="pronoun">Pronoun</option>
              <option value="preposition">Preposition</option>
              <option value="conjunction">Conjunction</option>
              <option value="interjection">Interjection</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="definition">Definition *</label>
          <textarea
            id="definition"
            name="definition"
            value={formData.definition}
            onChange={handleChange}
            required
            rows={3}
            placeholder="Primary definition of the word"
          />
        </div>

        <div className="form-group">
          <label htmlFor="literal_translation">Literal Translation</label>
          <textarea
            id="literal_translation"
            name="literal_translation"
            value={formData.literal_translation || ''}
            onChange={handleChange}
            rows={2}
            placeholder="Word-for-word meaning"
          />
        </div>

        <div className="form-group">
          <label htmlFor="context_notes">Context Notes</label>
          <textarea
            id="context_notes"
            name="context_notes"
            value={formData.context_notes || ''}
            onChange={handleChange}
            rows={3}
            placeholder="Cultural or contextual information"
          />
        </div>

        <div className="form-group">
          <label htmlFor="usage_examples">Usage Examples</label>
          <textarea
            id="usage_examples"
            name="usage_examples"
            value={formData.usage_examples || ''}
            onChange={handleChange}
            rows={3}
            placeholder="Example sentences using this word"
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/words')} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Word'}
          </button>
        </div>
      </form>
    </div>
  );
}

