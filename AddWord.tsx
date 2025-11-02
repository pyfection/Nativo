import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import wordService, { CreateWordData } from '../services/wordService';
import languageService, { LanguageListItem } from '../services/languageService';
import './AddWord.css';

export default function AddWord() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [languages, setLanguages] = useState<LanguageListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<CreateWordData>({
    word: '',
    language_id: '',
    definition: '',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchLanguages = async () => {
      try {
        const langs = await languageService.getAll();
        setLanguages(langs);
        if (langs.length > 0) {
          setFormData(prev => ({ ...prev, language_id: langs[0].id }));
        }
      } catch (err) {
        console.error('Failed to fetch languages:', err);
      }
    };

    fetchLanguages();
  }, [isAuthenticated, navigate]);

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
        <p>Contribute to preserving endangered languages by adding new words</p>
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

          <div className="form-group">
            <label htmlFor="language_id">Language *</label>
            <select
              id="language_id"
              name="language_id"
              value={formData.language_id}
              onChange={handleChange}
              required
            >
              <option value="">Select a language</option>
              {languages.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.name} {lang.native_name && `(${lang.native_name})`}
                </option>
              ))}
            </select>
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

