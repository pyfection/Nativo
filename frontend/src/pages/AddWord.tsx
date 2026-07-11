import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { Language } from '../App';
import wordService, { CreateLexemeData } from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
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

interface AdditionalFormDraft {
  form: string;
  romanization: string;
  ipa_pronunciation: string;
  plurality: string;
  grammatical_case: string;
  verb_aspect: string;
  notes: string;
}

const EMPTY_ADDITIONAL_FORM: AdditionalFormDraft = {
  form: '',
  romanization: '',
  ipa_pronunciation: '',
  plurality: '',
  grammatical_case: '',
  verb_aspect: '',
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
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState<FormState>(EMPTY_FORM);
  const [tagsInput, setTagsInput] = useState('');
  // Optional inflected forms entered on the same screen so a contributor can
  // capture a full paradigm in one submit. Each item becomes an additional
  // WordForm under the new Lexeme; lemma_form (above) stays the canonical one.
  const [additionalForms, setAdditionalForms] = useState<AdditionalFormDraft[]>([]);

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

      // Filter additional-form drafts down to those the user actually filled
      // in, then build CreateWordFormNested payloads omitting empty optional
      // fields (matches the backend nullable expectations).
      const additional = additionalForms
        .map((f) => ({ ...f, form: trim(f.form) }))
        .filter((f) => f.form.length > 0)
        .map((f) => ({
          form: f.form,
          ...(trim(f.romanization) && { romanization: trim(f.romanization) }),
          ...(trim(f.ipa_pronunciation) && { ipa_pronunciation: trim(f.ipa_pronunciation) }),
          ...(f.plurality && { plurality: f.plurality }),
          ...(f.grammatical_case && { grammatical_case: f.grammatical_case }),
          ...(f.verb_aspect && { verb_aspect: f.verb_aspect }),
          ...(trim(f.notes) && { notes: trim(f.notes) }),
        }));

      const payload: CreateLexemeData = {
        language_id: selectedLanguage.id,
        lemma: trim(formData.lemma),
        lemma_form: lemmaForm,
        ...(additional.length > 0 && { additional_forms: additional }),
        ...(formData.part_of_speech && { part_of_speech: formData.part_of_speech }),
        ...(formData.gender && { gender: formData.gender }),
        ...(formData.animacy && { animacy: formData.animacy }),
        ...(formData.language_register && { language_register: formData.language_register }),
        ...(trim(formData.source) && { source: trim(formData.source) }),
        ...(trim(formData.notes) && { notes: trim(formData.notes) }),
        ...(tags.length > 0 && { tags }),
      };

      const created = await wordService.create(payload);
      // Land on the detail page so contributors can immediately add
      // translations / synonyms / antonyms without an extra click.
      navigate(`/words/${created.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('add_word.create_failed'));
    } finally {
      setLoading(false);
    }
  };

  // ---- Additional-form helpers ----
  const addAdditionalForm = () =>
    setAdditionalForms((prev) => [...prev, { ...EMPTY_ADDITIONAL_FORM }]);
  const updateAdditionalForm = (i: number, patch: Partial<AdditionalFormDraft>) =>
    setAdditionalForms((prev) => prev.map((f, idx) => (idx === i ? { ...f, ...patch } : f)));
  const removeAdditionalForm = (i: number) =>
    setAdditionalForms((prev) => prev.filter((_, idx) => idx !== i));

  return (
    <div className="add-word-page">
      <div className="page-header">
        <h1>{t('add_word.title')}</h1>
        <p>
          {t('add_word.adding_to')}{' '}
          <strong>{languageDisplayName(selectedLanguage)} ({selectedLanguage.nativeName})</strong>
        </p>
      </div>

      {/* Surface the orthography rules right before the contributor types the
          word — this is the moment they need them. */}
      {selectedLanguage.writingStandardDocumentId && (
        <div className="add-word-standard-hint">
          📖 {t('add_word.standard_hint_question', { language: languageDisplayName(selectedLanguage) })}{' '}
          <Link to={`/languages/${selectedLanguage.id}/standard`}>
            {t('add_word.standard_hint_link')}
          </Link>{' '}
          {t('add_word.standard_hint_after')}
        </div>
      )}

      <form onSubmit={handleSubmit} className="word-form">
        {error && <div className="error-message">{error}</div>}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="lemma">{t('add_word.lemma_label')}</label>
            <input
              type="text"
              id="lemma"
              name="lemma"
              value={formData.lemma}
              onChange={handleChange}
              required
              placeholder={t('add_word.lemma_placeholder')}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="romanization">{t('add_word.romanization_label')}</label>
            <input
              type="text"
              id="romanization"
              name="romanization"
              value={formData.romanization}
              onChange={handleChange}
              placeholder={t('add_word.romanization_placeholder')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="ipa_pronunciation">{t('add_word.ipa_label')}</label>
            <input
              type="text"
              id="ipa_pronunciation"
              name="ipa_pronunciation"
              value={formData.ipa_pronunciation}
              onChange={handleChange}
              placeholder={t('add_word.ipa_placeholder')}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="part_of_speech">{t('add_word.pos_label')}</label>
            <select
              id="part_of_speech"
              name="part_of_speech"
              value={formData.part_of_speech}
              onChange={handleChange}
            >
              <option value="">{t('add_word.select_placeholder')}</option>
              {PART_OF_SPEECH_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.pos_${v}`)}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="language_register">{t('add_word.register_label')}</label>
            <select
              id="language_register"
              name="language_register"
              value={formData.language_register}
              onChange={handleChange}
            >
              {REGISTER_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.register_${v}`)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="gender">{t('add_word.gender_label')}</label>
            <select id="gender" name="gender" value={formData.gender} onChange={handleChange}>
              <option value="">{t('add_word.select_placeholder')}</option>
              {GENDER_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.gender_${v}`)}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="animacy">{t('add_word.animacy_label')}</label>
            <select id="animacy" name="animacy" value={formData.animacy} onChange={handleChange}>
              <option value="">{t('add_word.select_placeholder')}</option>
              {ANIMACY_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.animacy_${v}`)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="plurality">{t('add_word.plurality_label')}</label>
            <select
              id="plurality"
              name="plurality"
              value={formData.plurality}
              onChange={handleChange}
            >
              <option value="">{t('add_word.select_placeholder')}</option>
              {PLURALITY_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.plurality_${v}`)}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="grammatical_case">{t('add_word.case_label')}</label>
            <select
              id="grammatical_case"
              name="grammatical_case"
              value={formData.grammatical_case}
              onChange={handleChange}
            >
              <option value="">{t('add_word.select_placeholder')}</option>
              {CASE_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.case_${v}`)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="verb_aspect">{t('add_word.aspect_label')}</label>
            <select
              id="verb_aspect"
              name="verb_aspect"
              value={formData.verb_aspect}
              onChange={handleChange}
            >
              <option value="">{t('add_word.select_placeholder')}</option>
              {VERB_ASPECT_OPTIONS.map(([v]) => (
                <option key={v} value={v}>{t(`add_word.aspect_${v}`)}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="source">{t('add_word.source_label')}</label>
          <input
            type="text"
            id="source"
            name="source"
            value={formData.source}
            onChange={handleChange}
            placeholder={t('add_word.source_placeholder')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">{t('add_word.notes_label')}</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            placeholder={t('add_word.notes_placeholder')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="tags">{t('add_word.tags_label')}</label>
          <input
            type="text"
            id="tags"
            name="tags"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder={t('add_word.tags_placeholder')}
          />
        </div>

        {/* Additional inflected forms — paradigm in one go.
            The lemma form is captured above; these are the variations. */}
        <fieldset className="additional-forms">
          <legend>
            {t('add_word.additional_forms_legend')}
            <span className="additional-forms-hint">
              {t('add_word.additional_forms_hint')}
            </span>
          </legend>
          {additionalForms.map((form, idx) => (
            <div key={idx} className="additional-form-row">
              <div className="form-row">
                <div className="form-group">
                  <label>{t('add_word.form_label')}</label>
                  <input
                    type="text"
                    value={form.form}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { form: e.target.value })
                    }
                    placeholder={t('add_word.form_placeholder')}
                  />
                </div>
                <div className="form-group">
                  <label>{t('add_word.romanization_label')}</label>
                  <input
                    type="text"
                    value={form.romanization}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { romanization: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>{t('add_word.ipa_short_label')}</label>
                  <input
                    type="text"
                    value={form.ipa_pronunciation}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { ipa_pronunciation: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>{t('add_word.form_plurality_label')}</label>
                  <select
                    value={form.plurality}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { plurality: e.target.value })
                    }
                  >
                    <option value="">—</option>
                    {PLURALITY_OPTIONS.map(([v]) => (
                      <option key={v} value={v}>
                        {t(`add_word.plurality_${v}`)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('add_word.form_case_label')}</label>
                  <select
                    value={form.grammatical_case}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { grammatical_case: e.target.value })
                    }
                  >
                    <option value="">—</option>
                    {CASE_OPTIONS.map(([v]) => (
                      <option key={v} value={v}>
                        {t(`add_word.case_${v}`)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('add_word.form_aspect_label')}</label>
                  <select
                    value={form.verb_aspect}
                    onChange={(e) =>
                      updateAdditionalForm(idx, { verb_aspect: e.target.value })
                    }
                  >
                    <option value="">—</option>
                    {VERB_ASPECT_OPTIONS.map(([v]) => (
                      <option key={v} value={v}>
                        {t(`add_word.aspect_${v}`)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>{t('add_word.form_notes_label')}</label>
                <input
                  type="text"
                  value={form.notes}
                  onChange={(e) =>
                    updateAdditionalForm(idx, { notes: e.target.value })
                  }
                  placeholder={t('add_word.form_notes_placeholder')}
                />
              </div>
              <div className="additional-form-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => removeAdditionalForm(idx)}
                  title={t('add_word.remove_form_title')}
                >
                  {t('add_word.remove')}
                </button>
              </div>
            </div>
          ))}
          <button
            type="button"
            className="btn-secondary additional-form-add"
            onClick={addAdditionalForm}
            title={t('add_word.add_form_title')}
          >
            {t('add_word.add_form')}
          </button>
        </fieldset>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/words')} className="btn-secondary">
            {t('add_word.cancel')}
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !formData.lemma.trim()}
          >
            {loading ? t('add_word.creating') : t('add_word.create_word')}
          </button>
        </div>
      </form>
    </div>
  );
}
