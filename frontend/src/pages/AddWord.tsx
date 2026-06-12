import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Language } from '../App';
import wordService, { CreateLexemeData } from '../services/wordService';
import './AddWord.css';

interface AddWordProps {
  selectedLanguage: Language;
}

interface FormState {
  lemma: string;
  romanization: string;
  ipa_pronunciation: string;
  part_of_speech: string;
  gender: string;
  animacy: string;
  plurality: string;
  grammatical_case: string;
  verb_aspect: string;
  language_register: string;
  source: string;
  notes: string;
}

const EMPTY_FORM: FormState = {
  lemma: '',
  romanization: '',
  ipa_pronunciation: '',
  part_of_speech: '',
  gender: '',
  animacy: '',
  plurality: '',
  grammatical_case: '',
  verb_aspect: '',
  language_register: 'neutral',
  source: '',
  notes: '',
};

const PART_OF_SPEECH_OPTIONS = [
  ['noun', 'Noun'],
  ['verb', 'Verb'],
  ['adjective', 'Adjective'],
  ['adverb', 'Adverb'],
  ['pronoun', 'Pronoun'],
  ['preposition', 'Preposition'],
  ['conjunction', 'Conjunction'],
  ['interjection', 'Interjection'],
  ['article', 'Article'],
  ['determiner', 'Determiner'],
  ['particle', 'Particle'],
  ['numeral', 'Numeral'],
  ['classifier', 'Classifier'],
  ['other', 'Other'],
];

const GENDER_OPTIONS = [
  ['masculine', 'Masculine'],
  ['feminine', 'Feminine'],
  ['neuter', 'Neuter'],
  ['common', 'Common'],
  ['animate', 'Animate'],
  ['inanimate', 'Inanimate'],
  ['not_applicable', 'Not applicable'],
];

const PLURALITY_OPTIONS = [
  ['singular', 'Singular'],
  ['plural', 'Plural'],
  ['dual', 'Dual'],
  ['trial', 'Trial'],
  ['paucal', 'Paucal'],
  ['collective', 'Collective'],
  ['not_applicable', 'Not applicable'],
];

const CASE_OPTIONS = [
  ['nominative', 'Nominative'],
  ['accusative', 'Accusative'],
  ['genitive', 'Genitive'],
  ['dative', 'Dative'],
  ['ablative', 'Ablative'],
  ['locative', 'Locative'],
  ['instrumental', 'Instrumental'],
  ['vocative', 'Vocative'],
  ['partitive', 'Partitive'],
  ['ergative', 'Ergative'],
  ['absolutive', 'Absolutive'],
  ['not_applicable', 'Not applicable'],
];

const VERB_ASPECT_OPTIONS = [
  ['perfective', 'Perfective'],
  ['imperfective', 'Imperfective'],
  ['progressive', 'Progressive'],
  ['continuous', 'Continuous'],
  ['habitual', 'Habitual'],
  ['perfect', 'Perfect'],
  ['not_applicable', 'Not applicable'],
];

const ANIMACY_OPTIONS = [
  ['animate', 'Animate'],
  ['inanimate', 'Inanimate'],
  ['human', 'Human'],
  ['non_human', 'Non-human'],
  ['not_applicable', 'Not applicable'],
];

const REGISTER_OPTIONS = [
  ['formal', 'Formal'],
  ['informal', 'Informal'],
  ['colloquial', 'Colloquial'],
  ['slang', 'Slang'],
  ['ceremonial', 'Ceremonial'],
  ['archaic', 'Archaic'],
  ['poetic', 'Poetic'],
  ['technical', 'Technical'],
  ['neutral', 'Neutral'],
];

export default function AddWord({ selectedLanguage }: AddWordProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<FormState>(EMPTY_FORM);
  const [tagsInput, setTagsInput] = useState('');

  useEffect(() => {
    if (!isAuthenticated) navigate('/login');
  }, [isAuthenticated, navigate]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const trim = (v: string) => v.trim();
      const tags = tagsInput
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      const lemmaForm = {
        form: trim(formData.lemma),
        is_lemma: true,
        ...(trim(formData.romanization) && { romanization: trim(formData.romanization) }),
        ...(trim(formData.ipa_pronunciation) && {
          ipa_pronunciation: trim(formData.ipa_pronunciation),
        }),
        ...(formData.plurality && { plurality: formData.plurality }),
        ...(formData.grammatical_case && { grammatical_case: formData.grammatical_case }),
        ...(formData.verb_aspect && { verb_aspect: formData.verb_aspect }),
      };

      const payload: CreateLexemeData = {
        language_id: selectedLanguage.id,
        lemma: trim(formData.lemma),
        lemma_form: lemmaForm,
        ...(formData.part_of_speech && { part_of_speech: formData.part_of_speech }),
        ...(formData.gender && { gender: formData.gender }),
        ...(formData.animacy && { animacy: formData.animacy }),
        ...(formData.language_register && { language_register: formData.language_register }),
        ...(trim(formData.source) && { source: trim(formData.source) }),
        ...(trim(formData.notes) && { notes: trim(formData.notes) }),
        ...(tags.length > 0 && { tags }),
      };

      await wordService.create(payload);
      navigate('/words');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create word');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-word-page">
      <div className="page-header">
        <h1>Add New Word</h1>
        <p>
          Adding word to: <strong>{selectedLanguage.name} ({selectedLanguage.nativeName})</strong>
        </p>
      </div>

      <form onSubmit={handleSubmit} className="word-form">
        {error && <div className="error-message">{error}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="lemma">Lemma (canonical form) *</label>
            <input
              type="text"
              id="lemma"
              name="lemma"
              value={formData.lemma}
              onChange={handleChange}
              required
              placeholder="Citation form of the word"
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
              value={formData.romanization}
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
              value={formData.ipa_pronunciation}
              onChange={handleChange}
              placeholder="e.g. kˈæt"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="part_of_speech">Part of Speech</label>
            <select
              id="part_of_speech"
              name="part_of_speech"
              value={formData.part_of_speech}
              onChange={handleChange}
            >
              <option value="">Select…</option>
              {PART_OF_SPEECH_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="language_register">Register</label>
            <select
              id="language_register"
              name="language_register"
              value={formData.language_register}
              onChange={handleChange}
            >
              {REGISTER_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="gender">Gender</label>
            <select id="gender" name="gender" value={formData.gender} onChange={handleChange}>
              <option value="">Select…</option>
              {GENDER_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="animacy">Animacy</label>
            <select id="animacy" name="animacy" value={formData.animacy} onChange={handleChange}>
              <option value="">Select…</option>
              {ANIMACY_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="plurality">Plurality (this form)</label>
            <select
              id="plurality"
              name="plurality"
              value={formData.plurality}
              onChange={handleChange}
            >
              <option value="">Select…</option>
              {PLURALITY_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="grammatical_case">Grammatical Case (this form)</label>
            <select
              id="grammatical_case"
              name="grammatical_case"
              value={formData.grammatical_case}
              onChange={handleChange}
            >
              <option value="">Select…</option>
              {CASE_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="verb_aspect">Verb Aspect (this form)</label>
            <select
              id="verb_aspect"
              name="verb_aspect"
              value={formData.verb_aspect}
              onChange={handleChange}
            >
              <option value="">Select…</option>
              {VERB_ASPECT_OPTIONS.map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="source">Source / Citation</label>
          <input
            type="text"
            id="source"
            name="source"
            value={formData.source}
            onChange={handleChange}
            placeholder="Where this word was documented"
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">Internal Notes</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            placeholder="Editorial notes, not shown to the public"
          />
        </div>

        <div className="form-group">
          <label htmlFor="tags">Tags (comma-separated)</label>
          <input
            type="text"
            id="tags"
            name="tags"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="e.g. nature, ceremonial"
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/words')} className="btn-secondary">
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !formData.lemma.trim()}
          >
            {loading ? 'Creating…' : 'Create Word'}
          </button>
        </div>
      </form>
    </div>
  );
}
