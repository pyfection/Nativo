import { forwardRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../../App';
import { LexemeSuggestion, ReviewCorrections } from '../../services/wordService';

const PARTS_OF_SPEECH = [
  'noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction',
  'interjection', 'article', 'determiner', 'particle', 'numeral', 'other',
];

interface WordReviewCardProps {
  item: LexemeSuggestion;
  active: boolean;
  editing: boolean;
  busy: boolean;
  /** Languages a gloss can be edited in: those it has, plus the default. */
  glossLanguages: Language[];
  onFocus: () => void;
  onApprove: (corrections?: ReviewCorrections) => void;
  onReject: () => void;
  onEdit: () => void;
  onCancelEdit: () => void;
}

interface FormDraft {
  id: string;
  form: string;
  notes: string;
  isLemma: boolean;
  remove: boolean;
}

const splitGlosses = (value: string) =>
  value.split(',').map((g) => g.trim()).filter(Boolean);

/**
 * One suggested word in the review queue: everything needed to judge it at a
 * glance (glosses, forms, the drafter's evidence and example), plus an inline
 * editor so a nearly-right draft is fixed and approved in one step.
 */
const WordReviewCard = forwardRef<HTMLLIElement, WordReviewCardProps>(function WordReviewCard(
  { item, active, editing, busy, glossLanguages, onFocus, onApprove, onReject, onEdit, onCancelEdit },
  ref,
) {
  const { t } = useTranslation();
  const posLabel = (pos: string) => t(`words_page.pos_${pos}`, { defaultValue: pos });
  const glossesIn = (languageId: string) =>
    item.translations.filter((tr) => tr.language_id === languageId).map((tr) => tr.lemma);

  const otherForms = item.forms.filter((f) => !f.is_lemma);
  const classes = ['review-item', 'review-word', active ? 'is-active' : '', editing ? 'is-editing' : '']
    .filter(Boolean)
    .join(' ');

  return (
    <li ref={ref} className={classes} onClick={onFocus}>
      {editing ? (
        <WordEditor
          item={item}
          busy={busy}
          glossLanguages={glossLanguages}
          glossesIn={glossesIn}
          posLabel={posLabel}
          onSave={onApprove}
          onCancel={onCancelEdit}
        />
      ) : (
        <>
          <div className="review-item-main">
            <Link to={`/words/${item.id}`} className="review-item-lemma">
              {item.lemma}
            </Link>
            {item.part_of_speech && (
              <span className="review-item-pos">{posLabel(item.part_of_speech)}</span>
            )}
            {item.draft_confidence && (
              <span className={`review-confidence confidence-${item.draft_confidence}`}>
                {t(`review.confidence_${item.draft_confidence}`)}
              </span>
            )}
          </div>
          <div className="review-item-actions">
            <button type="button" className="btn-approve" disabled={busy} onClick={() => onApprove()}>
              {t('review.approve')}
            </button>
            <button type="button" className="btn-edit" disabled={busy} onClick={onEdit}>
              {t('review.edit')}
            </button>
            <button type="button" className="btn-reject" disabled={busy} onClick={onReject}>
              {t('review.reject')}
            </button>
          </div>
          {item.translations.length > 0 && (
            <p className="review-item-glosses">
              → {item.translations.map((tr) => tr.lemma).join(', ')}
            </p>
          )}
          {otherForms.length > 0 && (
            <p className="review-item-forms">
              {otherForms.map((f, i) => (
                <span key={f.id}>
                  {i > 0 && ', '}
                  <strong>{f.form}</strong>
                  {f.notes && <span className="review-form-note"> ({f.notes})</span>}
                </span>
              ))}
            </p>
          )}
          {item.notes && <p className="review-item-notes">{item.notes}</p>}
          <div className="review-item-meta">
            {item.creator_username && (
              <span>{t('review.suggested_by', { username: item.creator_username })}</span>
            )}
            {item.source && <span> · {item.source}</span>}
          </div>
        </>
      )}
    </li>
  );
});

interface WordEditorProps {
  item: LexemeSuggestion;
  busy: boolean;
  glossLanguages: Language[];
  glossesIn: (languageId: string) => string[];
  posLabel: (pos: string) => string;
  onSave: (corrections: ReviewCorrections) => void;
  onCancel: () => void;
}

function WordEditor({ item, busy, glossLanguages, glossesIn, posLabel, onSave, onCancel }: WordEditorProps) {
  const { t } = useTranslation();
  const [lemma, setLemma] = useState(item.lemma);
  const [pos, setPos] = useState(item.part_of_speech ?? '');
  const [notes, setNotes] = useState(item.notes ?? '');
  const [glosses, setGlosses] = useState<Record<string, string>>(() =>
    Object.fromEntries(glossLanguages.map((lang) => [lang.id, glossesIn(lang.id).join(', ')])),
  );
  const [forms, setForms] = useState<FormDraft[]>(() =>
    item.forms
      .filter((f) => !f.is_lemma)
      .map((f) => ({ id: f.id, form: f.form, notes: f.notes ?? '', isLemma: false, remove: false })),
  );

  const updateForm = (id: string, patch: Partial<FormDraft>) =>
    setForms((prev) => prev.map((f) => (f.id === id ? { ...f, ...patch } : f)));

  /** Send only what changed, so an untouched field never overwrites anything. */
  const buildCorrections = (): ReviewCorrections => {
    const corrections: ReviewCorrections = {};
    if (lemma.trim() && lemma.trim() !== item.lemma) corrections.lemma = lemma.trim();
    if (pos !== (item.part_of_speech ?? '')) corrections.part_of_speech = pos || null;
    if (notes !== (item.notes ?? '')) corrections.notes = notes || null;

    const formFixes = forms.flatMap((draft) => {
      const original = item.forms.find((f) => f.id === draft.id)!;
      if (draft.remove) return [{ id: draft.id, delete: true }];
      const fix: { id: string; form?: string; notes?: string | null } = { id: draft.id };
      if (draft.form.trim() && draft.form.trim() !== original.form) fix.form = draft.form.trim();
      if (draft.notes !== (original.notes ?? '')) fix.notes = draft.notes || null;
      return Object.keys(fix).length > 1 ? [fix] : [];
    });
    if (formFixes.length) corrections.forms = formFixes;

    const glossFixes = glossLanguages.flatMap((lang) => {
      const wanted = splitGlosses(glosses[lang.id] ?? '');
      const current = glossesIn(lang.id);
      const same = wanted.length === current.length && wanted.every((g) => current.includes(g));
      return same ? [] : [{ language_id: lang.id, lemmas: wanted }];
    });
    if (glossFixes.length) corrections.glosses = glossFixes;
    return corrections;
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(buildCorrections());
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onSave(buildCorrections());
    }
  };

  return (
    <form className="review-editor" onSubmit={submit} onKeyDown={onKeyDown}>
      <div className="review-editor-row">
        <label>
          <span>{t('review.field_lemma')}</span>
          <input autoFocus value={lemma} onChange={(e) => setLemma(e.target.value)} required />
        </label>
        <label>
          <span>{t('review.field_pos')}</span>
          <select value={pos} onChange={(e) => setPos(e.target.value)}>
            <option value="">—</option>
            {PARTS_OF_SPEECH.map((value) => (
              <option key={value} value={value}>
                {posLabel(value)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {glossLanguages.map((lang) => (
        <label key={lang.id} className="review-editor-wide">
          <span>{t('review.field_glosses', { language: lang.name })}</span>
          <input
            value={glosses[lang.id] ?? ''}
            onChange={(e) => setGlosses((prev) => ({ ...prev, [lang.id]: e.target.value }))}
          />
        </label>
      ))}

      {forms.length > 0 && (
        <fieldset className="review-editor-forms">
          <legend>{t('review.field_forms')}</legend>
          {forms.map((f) => (
            <div key={f.id} className={`review-editor-form${f.remove ? ' is-removed' : ''}`}>
              <input
                value={f.form}
                disabled={f.remove}
                onChange={(e) => updateForm(f.id, { form: e.target.value })}
                aria-label={t('review.field_forms')}
              />
              <input
                value={f.notes}
                disabled={f.remove}
                placeholder={t('review.form_note_placeholder')}
                onChange={(e) => updateForm(f.id, { notes: e.target.value })}
              />
              <label className="review-editor-remove">
                <input
                  type="checkbox"
                  checked={f.remove}
                  onChange={(e) => updateForm(f.id, { remove: e.target.checked })}
                />
                {t('review.remove_form')}
              </label>
            </div>
          ))}
        </fieldset>
      )}

      <label className="review-editor-wide">
        <span>{t('review.field_notes')}</span>
        <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>

      <div className="review-item-actions">
        <button type="submit" className="btn-approve" disabled={busy}>
          {t('review.save_approve')}
        </button>
        <button type="button" className="btn-edit" onClick={onCancel}>
          {t('review.cancel')}
        </button>
      </div>
    </form>
  );
}

export default WordReviewCard;
