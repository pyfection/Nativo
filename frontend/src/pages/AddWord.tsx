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
    language_register: 'neutral',
  });
  const [tagsInput, setTagsInput] = useState('');

  const parseTags = (value: string): string[] =>
    value
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);

  const PART_OF_SPEECH_OPTIONS = [
    { value: 'noun', label: 'Noun' },
    { value: 'verb', label: 'Verb' },
    { value: 'adjective', label: 'Adjective' },
    { value: 'adverb', label: 'Adverb' },
    { value: 'pronoun', label: 'Pronoun' },
    { value: 'preposition', label: 'Preposition' },
    { value: 'conjunction', label: 'Conjunction' },
    { value: 'interjection', label: 'Interjection' },
    { value: 'article', label: 'Article' },
    { value: 'determiner', label: 'Determiner' },
    { value: 'particle', label: 'Particle' },
    { value: 'numeral', label: 'Numeral' },
    { value: 'classifier', label: 'Classifier' },
    { value: 'other', label: 'Other' },
  ];

  const GENDER_OPTIONS = [
    { value: 'masculine', label: 'Masculine' },
    { value: 'feminine', label: 'Feminine' },
    { value: 'neuter', label: 'Neuter' },
    { value: 'common', label: 'Common' },
    { value: 'animate', label: 'Animate' },
    { value: 'inanimate', label: 'Inanimate' },
    { value: 'not_applicable', label: 'Not applicable' },
  ];

  const PLURALITY_OPTIONS = [
    { value: 'singular', label: 'Singular' },
    { value: 'plural', label: 'Plural' },
    { value: 'dual', label: 'Dual' },
    { value: 'trial', label: 'Trial' },
    { value: 'paucal', label: 'Paucal' },
    { value: 'collective', label: 'Collective' },
    { value: 'not_applicable', label: 'Not applicable' },
  ];

  const CASE_OPTIONS = [
    { value: 'nominative', label: 'Nominative' },
    { value: 'accusative', label: 'Accusative' },
    { value: 'genitive', label: 'Genitive' },
    { value: 'dative', label: 'Dative' },
    { value: 'ablative', label: 'Ablative' },
    { value: 'locative', label: 'Locative' },
    { value: 'instrumental', label: 'Instrumental' },
    { value: 'vocative', label: 'Vocative' },
    { value: 'partitive', label: 'Partitive' },
    { value: 'comitative', label: 'Comitative' },
    { value: 'essive', label: 'Essive' },
    { value: 'translative', label: 'Translative' },
    { value: 'ergative', label: 'Ergative' },
    { value: 'absolutive', label: 'Absolutive' },
    { value: 'not_applicable', label: 'Not applicable' },
  ];

  const VERB_ASPECT_OPTIONS = [
    { value: 'perfective', label: 'Perfective' },
    { value: 'imperfective', label: 'Imperfective' },
    { value: 'progressive', label: 'Progressive' },
    { value: 'continuous', label: 'Continuous' },
    { value: 'habitual', label: 'Habitual' },
    { value: 'iterative', label: 'Iterative' },
    { value: 'inchoative', label: 'Inchoative' },
    { value: 'perfect', label: 'Perfect' },
    { value: 'prospective', label: 'Prospective' },
    { value: 'not_applicable', label: 'Not applicable' },
    { value: 'other', label: 'Other' },
  ];

  const ANIMACY_OPTIONS = [
    { value: 'animate', label: 'Animate' },
    { value: 'inanimate', label: 'Inanimate' },
    { value: 'human', label: 'Human' },
    { value: 'non_human', label: 'Non-human' },
    { value: 'personal', label: 'Personal' },
    { value: 'impersonal', label: 'Impersonal' },
    { value: 'not_applicable', label: 'Not applicable' },
  ];

  const REGISTER_OPTIONS = [
    { value: 'formal', label: 'Formal' },
    { value: 'informal', label: 'Informal' },
    { value: 'colloquial', label: 'Colloquial' },
    { value: 'slang', label: 'Slang' },
    { value: 'ceremonial', label: 'Ceremonial' },
    { value: 'archaic', label: 'Archaic' },
    { value: 'taboo', label: 'Taboo' },
    { value: 'poetic', label: 'Poetic' },
    { value: 'technical', label: 'Technical' },
    { value: 'neutral', label: 'Neutral' },
  ];

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
      const tags = parseTags(tagsInput);
      const payload: CreateWordData = {
        word: formData.word.trim(),
        language_id: formData.language_id,
      };

      const optionalFields: Array<keyof CreateWordData> = [
        'romanization',
        'ipa_pronunciation',
        'part_of_speech',
        'gender',
        'plurality',
        'grammatical_case',
        'verb_aspect',
        'animacy',
        'language_register',
        'definition',
        'literal_translation',
        'context_notes',
        'usage_examples',
      ];

      optionalFields.forEach((field) => {
        const value = formData[field];
        if (typeof value === 'string') {
          const trimmed = value.trim();
          if (trimmed) {
            payload[field] = trimmed as any;
          }
        } else if (value) {
          payload[field] = value;
        }
      });

      if (tags.length > 0) {
        payload.tags = tags;
      }

      await wordService.create(payload);
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
              {PART_OF_SPEECH_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="definition">Definition</label>
          <textarea
            id="definition"
            name="definition"
            value={formData.definition || ''}
            onChange={handleChange}
            rows={3}
            placeholder="Primary definition of the word"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="gender">Gender</label>
            <select
              id="gender"
              name="gender"
              value={formData.gender || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {GENDER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="plurality">Plurality</label>
            <select
              id="plurality"
              name="plurality"
              value={formData.plurality || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {PLURALITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="grammatical_case">Grammatical Case</label>
            <select
              id="grammatical_case"
              name="grammatical_case"
              value={formData.grammatical_case || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {CASE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="verb_aspect">Verb Aspect</label>
            <select
              id="verb_aspect"
              name="verb_aspect"
              value={formData.verb_aspect || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {VERB_ASPECT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="animacy">Animacy</label>
            <select
              id="animacy"
              name="animacy"
              value={formData.animacy || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {ANIMACY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="language_register">Language Register</label>
            <select
              id="language_register"
              name="language_register"
              value={formData.language_register || ''}
              onChange={handleChange}
            >
              <option value="">Select...</option>
              {REGISTER_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
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

        <div className="form-group">
          <label htmlFor="tags">Tags (comma separated)</label>
          <input
            type="text"
            id="tags"
            name="tags"
            value={tagsInput}
            onChange={(event) => setTagsInput(event.target.value)}
            placeholder="e.g., nature, ceremonial"
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/words')} className="btn-secondary">
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !formData.word.trim()}
          >
            {loading ? 'Creating...' : 'Create Word'}
          </button>
        </div>
      </form>
    </div>
  );
}

