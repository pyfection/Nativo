import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import AudioRecorder from '../components/common/AudioRecorder';
import SpellingVariants from '../components/common/SpellingVariants';
import { useAuth } from '../contexts/AuthContext';
import wordService, {
  AntonymLink,
  CreateWordFormData,
  LexemeWithForms,
  SynonymLink,
  TranslationLink,
  UpdateWordFormData,
  WordForm,
} from '../services/wordService';
import { languageDisplayName } from '../utils/languageName';
import './WordDetail.css';

interface WordDetailProps {
  selectedLanguage: Language;
  languages: Language[];
}

const PLURALITY_OPTIONS = [
  '', 'singular', 'plural', 'dual', 'trial', 'paucal', 'collective', 'not_applicable',
];
const CASE_OPTIONS = [
  '', 'nominative', 'accusative', 'genitive', 'dative', 'ablative', 'locative',
  'instrumental', 'vocative', 'partitive', 'ergative', 'absolutive', 'not_applicable',
];
const ASPECT_OPTIONS = [
  '', 'perfective', 'imperfective', 'progressive', 'continuous', 'habitual',
  'perfect', 'not_applicable',
];

/**
 * Dictionary entry detail page — the long-missing /words/:id surface.
 *
 * Shows the lexeme header (lemma, POS, status), its full list of WordForms
 * (lemma + inflections), and its cross-language Translations / Synonyms /
 * Antonyms. Forms and links are editable inline when the user has edit
 * permission on the lexeme's language.
 */
export default function WordDetail({ languages }: WordDetailProps) {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { canEditLanguage } = useAuth();

  const [lexeme, setLexeme] = useState<LexemeWithForms | null>(null);
  const [translations, setTranslations] = useState<TranslationLink[]>([]);
  const [synonyms, setSynonyms] = useState<SynonymLink[]>([]);
  const [antonyms, setAntonyms] = useState<AntonymLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const language = lexeme && languages.find((l) => l.id === lexeme.language_id);
  const canEdit = lexeme ? canEditLanguage(lexeme.language_id) : false;

  // Load the lexeme + all its relations.
  const refresh = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [lex, tr, syn, ant] = await Promise.all([
        wordService.getById(id),
        wordService.listTranslations(id).catch(() => []),
        wordService.listSynonyms(id).catch(() => []),
        wordService.listAntonyms(id).catch(() => []),
      ]);
      setLexeme(lex);
      setTranslations(tr);
      setSynonyms(syn);
      setAntonyms(ant);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('word_detail.load_failed'));
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto-dismiss toasts.
  useEffect(() => {
    if (!actionMessage) return;
    const timer = setTimeout(() => setActionMessage(null), 4000);
    return () => clearTimeout(timer);
  }, [actionMessage]);
  useEffect(() => {
    if (!actionError) return;
    const timer = setTimeout(() => setActionError(null), 8000);
    return () => clearTimeout(timer);
  }, [actionError]);

  if (loading) {
    return (
      <div className="word-detail-page">
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>{t('word_detail.loading')}</p>
        </div>
      </div>
    );
  }

  if (error || !lexeme) {
    return (
      <div className="word-detail-page">
        <div className="error-state">
          <p>{error ?? t('word_detail.not_found')}</p>
          <Link to="/words" className="btn btn-ghost">
            {t('word_detail.back_to_words')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="word-detail-page">
      <header className="word-detail-header">
        <button
          type="button"
          className="btn-link"
          onClick={() => navigate('/words')}
          title={t('word_detail.back_to_words_title')}
        >
          {t('word_detail.back_to_words')}
        </button>
        <div className="word-detail-title-row">
          <h1 className="word-detail-lemma">{lexeme.lemma}</h1>
          {lexeme.part_of_speech && (
            <span className="word-detail-pos">{lexeme.part_of_speech}</span>
          )}
          {lexeme.gender && (
            <span className="word-detail-tag">{lexeme.gender}</span>
          )}
          <span className={`status-badge status-${lexeme.status}`}>
            {lexeme.status.replace('_', ' ')}
          </span>
          {lexeme.is_verified && (
            <span className="status-badge status-verified" title={t('word_detail.verified_title')}>
              {t('word_detail.verified_badge')}
            </span>
          )}
        </div>
        {language && (
          <p className="word-detail-language">
            {languageDisplayName(language)} <span className="muted">· {language.nativeName}</span>
            {language.writingStandardDocumentId && (
              <>
                {' · '}
                <Link
                  to={`/languages/${language.id}/standard`}
                  className="word-detail-standard-link"
                  title={t('word_detail.standard_link_title', {
                    language: languageDisplayName(language),
                  })}
                >
                  📖 {t('word_detail.standard_link')}
                </Link>
              </>
            )}
          </p>
        )}
        {lexeme.notes && <p className="word-detail-notes">{lexeme.notes}</p>}
      </header>

      <FormsSection
        lexeme={lexeme}
        canEdit={canEdit}
        onChange={refresh}
        onMessage={setActionMessage}
        onError={setActionError}
      />

      <RelationsSection
        title={t('word_detail.translations')}
        addButtonTitle={t('word_detail.add_translation_title')}
        items={translations.map((tr) => ({
          id: tr.id,
          lemma: tr.lemma,
          language_id: tr.language_id,
          language_name: tr.language_name ?? languages.find((l) => l.id === tr.language_id)?.name,
          notes: tr.notes,
        }))}
        emptyHint={t('word_detail.translations_empty_hint')}
        searchLanguageIds={languages
          .filter((l) => l.id !== lexeme.language_id)
          .map((l) => l.id)
          .join(',')}
        canEdit={canEdit}
        canAdd
        excludeSameLanguage
        languages={languages}
        onAdd={async (otherId) => {
          await wordService.addTranslation(lexeme.id, { other_lexeme_id: otherId });
          const refreshed = await wordService.listTranslations(lexeme.id);
          setTranslations(refreshed);
          setActionMessage(t('word_detail.translation_linked'));
        }}
        onRemove={async (otherId) => {
          await wordService.removeTranslation(lexeme.id, otherId);
          setTranslations((prev) => prev.filter((tr) => tr.id !== otherId));
          setActionMessage(t('word_detail.translation_removed'));
        }}
        onError={setActionError}
      />

      <RelationsSection
        title={t('word_detail.synonyms')}
        addButtonTitle={t('word_detail.add_synonym_title')}
        items={synonyms.map((s) => ({
          id: s.id,
          lemma: s.lemma,
          language_id: s.language_id,
          language_name: s.language_name ?? languages.find((l) => l.id === s.language_id)?.name,
          notes: s.nuance ? `(${s.nuance})${s.notes ? ' ' + s.notes : ''}` : s.notes,
        }))}
        emptyHint={t('word_detail.synonyms_empty_hint')}
        searchLanguageIds={lexeme.language_id}
        canEdit={canEdit}
        canAdd
        languages={languages}
        onAdd={async (otherId) => {
          await wordService.addSynonym(lexeme.id, { other_lexeme_id: otherId });
          const refreshed = await wordService.listSynonyms(lexeme.id);
          setSynonyms(refreshed);
          setActionMessage(t('word_detail.synonym_linked'));
        }}
        onRemove={async (otherId) => {
          await wordService.removeSynonym(lexeme.id, otherId);
          setSynonyms((prev) => prev.filter((s) => s.id !== otherId));
          setActionMessage(t('word_detail.synonym_removed'));
        }}
        onError={setActionError}
      />

      <RelationsSection
        title={t('word_detail.antonyms')}
        addButtonTitle={t('word_detail.add_antonym_title')}
        items={antonyms.map((a) => ({
          id: a.id,
          lemma: a.lemma,
          language_id: a.language_id,
          language_name: a.language_name ?? languages.find((l) => l.id === a.language_id)?.name,
          notes: a.antonym_type ? `(${a.antonym_type})${a.notes ? ' ' + a.notes : ''}` : a.notes,
        }))}
        emptyHint={t('word_detail.antonyms_empty_hint')}
        searchLanguageIds={lexeme.language_id}
        canEdit={canEdit}
        canAdd
        languages={languages}
        onAdd={async (otherId) => {
          await wordService.addAntonym(lexeme.id, { other_lexeme_id: otherId });
          const refreshed = await wordService.listAntonyms(lexeme.id);
          setAntonyms(refreshed);
          setActionMessage(t('word_detail.antonym_linked'));
        }}
        onRemove={async (otherId) => {
          await wordService.removeAntonym(lexeme.id, otherId);
          setAntonyms((prev) => prev.filter((a) => a.id !== otherId));
          setActionMessage(t('word_detail.antonym_removed'));
        }}
        onError={setActionError}
      />

      {(actionError || actionMessage) && (
        <div className="word-detail-toasts" role="status" aria-live="polite">
          {actionError && (
            <div className="word-detail-toast toast-error">
              <span className="toast-body">{actionError}</span>
              <button
                type="button"
                className="toast-dismiss"
                onClick={() => setActionError(null)}
                aria-label={t('word_detail.dismiss')}
                title={t('word_detail.dismiss')}
              >
                ×
              </button>
            </div>
          )}
          {actionMessage && (
            <div className="word-detail-toast toast-success">
              <span className="toast-body">{actionMessage}</span>
              <button
                type="button"
                className="toast-dismiss"
                onClick={() => setActionMessage(null)}
                aria-label={t('word_detail.dismiss')}
                title={t('word_detail.dismiss')}
              >
                ×
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Forms section — CRUD over WordForm rows
// ---------------------------------------------------------------------------

interface FormsSectionProps {
  lexeme: LexemeWithForms;
  canEdit: boolean;
  onChange: () => Promise<void>;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
}

function FormsSection({ lexeme, canEdit, onChange, onMessage, onError }: FormsSectionProps) {
  const { t } = useTranslation();
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState<UpdateWordFormData>({});
  const [busy, setBusy] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<UpdateWordFormData>({});

  const handleAdd = async () => {
    if (!draft.form?.trim()) return;
    setBusy(true);
    try {
      const payload: CreateWordFormData = {
        lexeme_id: lexeme.id,
        form: draft.form.trim(),
        ...(draft.romanization?.trim() && { romanization: draft.romanization.trim() }),
        ...(draft.ipa_pronunciation?.trim() && { ipa_pronunciation: draft.ipa_pronunciation.trim() }),
        ...(draft.plurality && { plurality: draft.plurality }),
        ...(draft.grammatical_case && { grammatical_case: draft.grammatical_case }),
        ...(draft.verb_aspect && { verb_aspect: draft.verb_aspect }),
        ...(draft.notes?.trim() && { notes: draft.notes.trim() }),
      };
      await wordService.addForm(lexeme.id, payload);
      await onChange();
      setShowAdd(false);
      setDraft({});
      onMessage(t('word_detail.form_added'));
    } catch (err: any) {
      onError(err.response?.data?.detail || t('word_detail.add_form_failed'));
    } finally {
      setBusy(false);
    }
  };

  const handleSaveEdit = async (formId: string) => {
    setBusy(true);
    try {
      const payload: UpdateWordFormData = {};
      if (editDraft.form?.trim()) payload.form = editDraft.form.trim();
      if (editDraft.romanization !== undefined)
        payload.romanization = editDraft.romanization || undefined;
      if (editDraft.ipa_pronunciation !== undefined)
        payload.ipa_pronunciation = editDraft.ipa_pronunciation || undefined;
      if (editDraft.plurality !== undefined) payload.plurality = editDraft.plurality || undefined;
      if (editDraft.grammatical_case !== undefined)
        payload.grammatical_case = editDraft.grammatical_case || undefined;
      if (editDraft.verb_aspect !== undefined)
        payload.verb_aspect = editDraft.verb_aspect || undefined;
      if (editDraft.notes !== undefined) payload.notes = editDraft.notes || undefined;
      await wordService.updateForm(formId, payload);
      await onChange();
      setEditingId(null);
      setEditDraft({});
      onMessage(t('word_detail.form_updated'));
    } catch (err: any) {
      onError(err.response?.data?.detail || t('word_detail.update_form_failed'));
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (form: WordForm) => {
    if (form.is_lemma) {
      onError(t('word_detail.cannot_delete_lemma'));
      return;
    }
    if (!window.confirm(t('word_detail.confirm_delete_form', { form: form.form }))) return;
    setBusy(true);
    try {
      await wordService.deleteForm(form.id);
      await onChange();
      onMessage(t('word_detail.form_deleted'));
    } catch (err: any) {
      onError(err.response?.data?.detail || t('word_detail.delete_form_failed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="word-detail-section">
      <div className="word-detail-section-header">
        <h2>{t('word_detail.forms_heading', { count: lexeme.forms?.length ?? 0 })}</h2>
        {canEdit && !showAdd && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setShowAdd(true)}
            title={t('word_detail.add_form_title')}
          >
            {t('word_detail.add_form')}
          </button>
        )}
      </div>

      <ul className="forms-list">
        {(lexeme.forms ?? []).map((form) => {
          const isEditing = editingId === form.id;
          return (
            <li key={form.id} className="form-row">
              {isEditing ? (
                <FormEditor
                  initial={form}
                  draft={editDraft}
                  setDraft={setEditDraft}
                  onSave={() => handleSaveEdit(form.id)}
                  onCancel={() => {
                    setEditingId(null);
                    setEditDraft({});
                  }}
                  busy={busy}
                />
              ) : (
                <>
                  <div className="form-row-main">
                    <span className="form-text">{form.form}</span>
                    {form.is_lemma && (
                      <span className="form-badge form-badge-lemma" title={t('word_detail.lemma_badge_title')}>
                        {t('word_detail.lemma_badge')}
                      </span>
                    )}
                    {form.romanization && (
                      <span className="form-roman">/{form.romanization}/</span>
                    )}
                    {form.ipa_pronunciation && (
                      <span className="form-ipa">[{form.ipa_pronunciation}]</span>
                    )}
                  </div>
                  {(form.plurality || form.grammatical_case || form.verb_aspect || form.notes) && (
                    <div className="form-row-meta">
                      {form.plurality && <span className="form-meta-chip">{form.plurality}</span>}
                      {form.grammatical_case && (
                        <span className="form-meta-chip">{form.grammatical_case}</span>
                      )}
                      {form.verb_aspect && (
                        <span className="form-meta-chip">{form.verb_aspect}</span>
                      )}
                      {form.notes && <span className="form-meta-note">{form.notes}</span>}
                    </div>
                  )}
                  {canEdit && (
                    <div className="form-row-actions">
                      <button
                        type="button"
                        className="btn btn-ghost btn-xs"
                        onClick={() => {
                          setEditingId(form.id);
                          setEditDraft({
                            form: form.form,
                            romanization: form.romanization,
                            ipa_pronunciation: form.ipa_pronunciation,
                            plurality: form.plurality,
                            grammatical_case: form.grammatical_case,
                            verb_aspect: form.verb_aspect,
                            notes: form.notes,
                          });
                        }}
                        title={t('word_detail.edit_form_title')}
                      >
                        {t('word_detail.edit')}
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-xs"
                        onClick={() => handleDelete(form)}
                        disabled={form.is_lemma}
                        title={
                          form.is_lemma
                            ? t('word_detail.lemma_delete_title')
                            : t('word_detail.delete_form_title')
                        }
                      >
                        {t('word_detail.delete')}
                      </button>
                    </div>
                  )}
                  {/* Per-form audio: a recorder + inline players for any
                      existing recordings linked to this WordForm. */}
                  <div className="form-row-audio">
                    <AudioRecorder
                      wordFormId={form.id}
                      canEdit={canEdit}
                      onMessage={onMessage}
                      onError={onError}
                    />
                  </div>
                  {/* Per-form spelling variants: non-standard ways this form
                      is written, mapped back to its standard spelling. */}
                  <div className="form-row-spellings">
                    <SpellingVariants
                      wordFormId={form.id}
                      canEdit={canEdit}
                      onMessage={onMessage}
                      onError={onError}
                    />
                  </div>
                </>
              )}
            </li>
          );
        })}
      </ul>

      {showAdd && (
        <div className="form-add">
          <FormEditor
            draft={draft}
            setDraft={setDraft}
            onSave={handleAdd}
            onCancel={() => {
              setShowAdd(false);
              setDraft({});
            }}
            busy={busy}
            isAdd
          />
        </div>
      )}
    </section>
  );
}

interface FormEditorProps {
  initial?: WordForm;
  draft: UpdateWordFormData;
  setDraft: (d: UpdateWordFormData) => void;
  onSave: () => void;
  onCancel: () => void;
  busy: boolean;
  isAdd?: boolean;
}

function FormEditor({ draft, setDraft, onSave, onCancel, busy, isAdd }: FormEditorProps) {
  const { t } = useTranslation();
  return (
    <div className="form-editor">
      <div className="form-editor-row">
        <label>
          {t('word_detail.form_label')}
          <input
            type="text"
            value={draft.form ?? ''}
            onChange={(e) => setDraft({ ...draft, form: e.target.value })}
            placeholder={t('word_detail.form_placeholder')}
            autoFocus
          />
        </label>
        <label>
          {t('word_detail.romanization_label')}
          <input
            type="text"
            value={draft.romanization ?? ''}
            onChange={(e) => setDraft({ ...draft, romanization: e.target.value })}
          />
        </label>
        <label>
          {t('word_detail.ipa_label')}
          <input
            type="text"
            value={draft.ipa_pronunciation ?? ''}
            onChange={(e) => setDraft({ ...draft, ipa_pronunciation: e.target.value })}
            placeholder={t('word_detail.ipa_placeholder')}
          />
        </label>
      </div>
      <div className="form-editor-row">
        <label>
          {t('word_detail.plurality_label')}
          <select
            value={draft.plurality ?? ''}
            onChange={(e) => setDraft({ ...draft, plurality: e.target.value })}
          >
            {PLURALITY_OPTIONS.map((o) => (
              <option key={o || 'none'} value={o}>
                {o || '—'}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t('word_detail.case_label')}
          <select
            value={draft.grammatical_case ?? ''}
            onChange={(e) => setDraft({ ...draft, grammatical_case: e.target.value })}
          >
            {CASE_OPTIONS.map((o) => (
              <option key={o || 'none'} value={o}>
                {o || '—'}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t('word_detail.verb_aspect_label')}
          <select
            value={draft.verb_aspect ?? ''}
            onChange={(e) => setDraft({ ...draft, verb_aspect: e.target.value })}
          >
            {ASPECT_OPTIONS.map((o) => (
              <option key={o || 'none'} value={o}>
                {o || '—'}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="form-editor-notes">
        {t('word_detail.notes_label')}
        <input
          type="text"
          value={draft.notes ?? ''}
          onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
          placeholder={t('word_detail.notes_placeholder')}
        />
      </label>
      <div className="form-editor-actions">
        <button
          type="button"
          className="btn btn-accent"
          onClick={onSave}
          disabled={busy || !draft.form?.trim()}
        >
          {isAdd ? t('word_detail.add') : t('word_detail.save')}
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onCancel}
          disabled={busy}
        >
          {t('word_detail.cancel')}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Translations / Synonyms / Antonyms
// ---------------------------------------------------------------------------

interface RelationItem {
  id: string;
  lemma: string;
  language_id: string;
  language_name?: string;
  notes?: string;
}

interface RelationsSectionProps {
  title: string;
  /** Tooltip for the "+ Add" button (already localized by the caller). */
  addButtonTitle: string;
  items: RelationItem[];
  emptyHint: string;
  /** Comma-separated language ids to constrain the picker search. */
  searchLanguageIds: string;
  canEdit: boolean;
  canAdd: boolean;
  excludeSameLanguage?: boolean;
  languages: Language[];
  onAdd: (otherLexemeId: string) => Promise<void>;
  onRemove: (otherLexemeId: string) => Promise<void>;
  onError: (msg: string) => void;
}

function RelationsSection({
  title,
  addButtonTitle,
  items,
  emptyHint,
  searchLanguageIds,
  canEdit,
  canAdd,
  languages,
  onAdd,
  onRemove,
  onError,
}: RelationsSectionProps) {
  const { t } = useTranslation();
  const [picking, setPicking] = useState(false);

  return (
    <section className="word-detail-section">
      <div className="word-detail-section-header">
        <h2>
          {title} ({items.length})
        </h2>
        {canEdit && canAdd && !picking && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setPicking(true)}
            title={addButtonTitle}
          >
            {t('word_detail.add_relation')}
          </button>
        )}
      </div>

      {items.length === 0 && !picking && (
        <p className="word-detail-empty">{emptyHint}</p>
      )}

      {items.length > 0 && (
        <ul className="relations-list">
          {items.map((item) => {
            const lang = languages.find((l) => l.id === item.language_id);
            return (
              <li key={item.id} className="relation-row">
                <Link
                  to={`/words/${item.id}`}
                  className="relation-lemma"
                  title={t('word_detail.open_word_title', { lemma: item.lemma })}
                >
                  {item.lemma}
                </Link>
                {lang && <span className="relation-language">{languageDisplayName(lang)}</span>}
                {item.notes && <span className="relation-notes">{item.notes}</span>}
                {canEdit && (
                  <button
                    type="button"
                    className="btn btn-ghost btn-xs relation-remove"
                    onClick={async () => {
                      try {
                        await onRemove(item.id);
                      } catch (err: any) {
                        onError(err.response?.data?.detail || t('word_detail.remove_failed'));
                      }
                    }}
                    title={t('word_detail.remove_link_title')}
                  >
                    {t('word_detail.remove')}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {picking && (
        <RelationPicker
          searchLanguageIds={searchLanguageIds}
          excludeIds={items.map((i) => i.id)}
          onPick={async (otherId) => {
            try {
              await onAdd(otherId);
              setPicking(false);
            } catch (err: any) {
              onError(err.response?.data?.detail || t('word_detail.add_failed'));
            }
          }}
          onCancel={() => setPicking(false)}
        />
      )}
    </section>
  );
}

interface RelationPickerProps {
  searchLanguageIds: string;
  excludeIds: string[];
  onPick: (otherLexemeId: string) => Promise<void>;
  onCancel: () => void;
}

function RelationPicker({ searchLanguageIds, excludeIds, onPick, onCancel }: RelationPickerProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LexemeWithForms[]>([]);
  const [searching, setSearching] = useState(false);

  // Debounced search as the user types.
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      setSearching(true);
      try {
        const r = await wordService.search({
          q,
          language_ids: searchLanguageIds,
          include_unpublished: true,
          limit: 10,
        });
        setResults(r.filter((x) => !excludeIds.includes(x.id)));
      } finally {
        setSearching(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [query, searchLanguageIds, excludeIds]);

  return (
    <div className="relation-picker">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={t('word_detail.picker_placeholder')}
        autoFocus
      />
      {searching && <p className="relation-picker-status">{t('word_detail.picker_searching')}</p>}
      {!searching && query.trim().length >= 2 && results.length === 0 && (
        <p className="relation-picker-status">{t('word_detail.picker_no_matches')}</p>
      )}
      {results.length > 0 && (
        <ul className="relation-picker-results">
          {results.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                className="relation-picker-result"
                onClick={() => onPick(r.id)}
              >
                <span className="relation-picker-lemma">{r.lemma}</span>
                {r.part_of_speech && (
                  <span className="relation-picker-pos">{r.part_of_speech}</span>
                )}
                {r.notes && <span className="relation-picker-notes">{r.notes}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      <button type="button" className="btn btn-ghost btn-sm" onClick={onCancel}>
        {t('word_detail.cancel')}
      </button>
    </div>
  );
}
