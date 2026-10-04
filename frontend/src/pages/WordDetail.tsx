import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import AudioRecorder from '../components/common/AudioRecorder';
import SpellingVariants from '../components/common/SpellingVariants';
import { useAuth } from '../contexts/AuthContext';
import proposalService, { ChangeProposal, VoteChoice } from '../services/proposalService';
import wordService, {
  AntonymLink,
  BORROWING_ORIGINS,
  CreateWordFormData,
  LEXEME_ORIGINS,
  LEXEME_RECOMMENDATIONS,
  LexemeOrigin,
  LexemeRecommendation,
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
  const { canEditLanguage, canVerifyLanguage, user } = useAuth();

  const [lexeme, setLexeme] = useState<LexemeWithForms | null>(null);
  const [translations, setTranslations] = useState<TranslationLink[]>([]);
  const [synonyms, setSynonyms] = useState<SynonymLink[]>([]);
  const [antonyms, setAntonyms] = useState<AntonymLink[]>([]);
  const [proposals, setProposals] = useState<ChangeProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const language = lexeme && languages.find((l) => l.id === lexeme.language_id);
  const borrowedFrom =
    lexeme?.borrowed_from_language_id &&
    languages.find((l) => l.id === lexeme.borrowed_from_language_id);
  const canEdit = lexeme ? canEditLanguage(lexeme.language_id) : false;
  const canVote = lexeme ? canEdit || canVerifyLanguage(lexeme.language_id) : false;
  const openProposal = proposals.find((p) => p.status === 'open');
  // "Tomadn" → point at the voted-preferred alternative ("Párádaisa").
  const preferredAlternatives =
    lexeme?.recommendation === 'preferred'
      ? []
      : synonyms.filter(
          (s) => s.recommendation === 'preferred' && s.language_id === lexeme?.language_id,
        );

  // Load the lexeme + all its relations.
  const refresh = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [lex, tr, syn, ant, props] = await Promise.all([
        wordService.getById(id),
        wordService.listTranslations(id).catch(() => []),
        wordService.listSynonyms(id).catch(() => []),
        wordService.listAntonyms(id).catch(() => []),
        proposalService.listForWord(id).catch(() => []),
      ]);
      setLexeme(lex);
      setTranslations(tr);
      setSynonyms(syn);
      setAntonyms(ant);
      setProposals(props);
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
          {lexeme.origin && (
            <span className="word-detail-tag word-detail-origin" title={t('add_word.origin_hint')}>
              {borrowedFrom
                ? t('word_detail.origin_from', {
                    origin: t(`add_word.origin_${lexeme.origin}`),
                    language: languageDisplayName(borrowedFrom),
                  })
                : t(`add_word.origin_${lexeme.origin}`)}
            </span>
          )}
          {lexeme.recommendation && lexeme.recommendation !== 'neutral' && (
            <span
              className={`status-badge recommendation-${lexeme.recommendation}`}
              title={t('word_detail.recommendation_by_vote')}
            >
              {t(`word_detail.recommendation_${lexeme.recommendation}`)}
            </span>
          )}
          {openProposal && (
            <a href="#proposals" className="status-badge recommendation-vote-open">
              {t('word_detail.vote_open')}
            </a>
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
        {lexeme.recommendation_note && lexeme.recommendation !== 'neutral' && (
          <p className="word-detail-recommendation-note">{lexeme.recommendation_note}</p>
        )}
        {preferredAlternatives.length > 0 && (
          <p className="word-detail-preferred-hint">
            {t('word_detail.preferred_alternative')}{' '}
            {preferredAlternatives.map((alt, i) => (
              <span key={alt.id}>
                {i > 0 && ', '}
                <Link to={`/words/${alt.id}`}>{alt.lemma}</Link>
              </span>
            ))}
          </p>
        )}
        {lexeme.notes && <p className="word-detail-notes">{lexeme.notes}</p>}
        {canEdit && (
          <OriginEditor
            lexeme={lexeme}
            languages={languages}
            onSaved={() => {
              setActionMessage(t('word_detail.origin_saved'));
              refresh();
            }}
            onError={setActionError}
          />
        )}
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
          lemma: s.recommendation === 'preferred' ? `${s.lemma} ★` : s.lemma,
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

      <ProposalsSection
        lexeme={lexeme}
        proposals={proposals}
        canPropose={canEdit}
        canVote={canVote}
        currentUserId={user?.id}
        onChange={refresh}
        onMessage={setActionMessage}
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

// ---------------------------------------------------------------------------
// Origin editor — native / loanword / calque / neologism (+ source language)
// ---------------------------------------------------------------------------

interface OriginEditorProps {
  lexeme: LexemeWithForms;
  languages: Language[];
  onSaved: () => void;
  onError: (msg: string) => void;
}

function OriginEditor({ lexeme, languages, onSaved, onError }: OriginEditorProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [origin, setOrigin] = useState<LexemeOrigin | ''>(lexeme.origin ?? '');
  const [sourceId, setSourceId] = useState(lexeme.borrowed_from_language_id ?? '');

  const isBorrowing = BORROWING_ORIGINS.includes(origin as LexemeOrigin);

  const startEditing = () => {
    setOrigin(lexeme.origin ?? '');
    setSourceId(lexeme.borrowed_from_language_id ?? '');
    setOpen(true);
  };

  const handleSave = async () => {
    setBusy(true);
    try {
      await wordService.update(lexeme.id, {
        origin: origin || null,
        // Only loanwords / calques keep a source language; clear it otherwise.
        borrowed_from_language_id: isBorrowing && sourceId ? sourceId : null,
      });
      setOpen(false);
      onSaved();
    } catch (err: any) {
      onError(err.response?.data?.detail || t('word_detail.origin_save_failed'));
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button
        type="button"
        className="btn btn-ghost btn-xs origin-edit-toggle"
        onClick={startEditing}
        title={t('add_word.origin_hint')}
      >
        {t('word_detail.edit_origin')}
      </button>
    );
  }

  return (
    <div className="form-editor origin-editor">
      <div className="form-editor-row">
        <label>
          {t('add_word.origin_label')}
          <select value={origin} onChange={(e) => setOrigin(e.target.value as LexemeOrigin | '')}>
            <option value="">—</option>
            {LEXEME_ORIGINS.map((o) => (
              <option key={o} value={o}>{t(`add_word.origin_${o}`)}</option>
            ))}
          </select>
        </label>
        {isBorrowing && (
          <label>
            {t('add_word.borrowed_from_label')}
            <select value={sourceId} onChange={(e) => setSourceId(e.target.value)}>
              <option value="">—</option>
              {languages
                .filter((l) => l.id !== lexeme.language_id)
                .map((l) => (
                  <option key={l.id} value={l.id}>{languageDisplayName(l)}</option>
                ))}
            </select>
          </label>
        )}
      </div>
      <div className="form-editor-actions">
        <button type="button" className="btn btn-accent" onClick={handleSave} disabled={busy}>
          {t('word_detail.save')}
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => setOpen(false)}
          disabled={busy}
        >
          {t('word_detail.cancel')}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recommendation proposals — preferred / discouraged is decided by vote
// ---------------------------------------------------------------------------

interface ProposalsSectionProps {
  lexeme: LexemeWithForms;
  proposals: ChangeProposal[];
  canPropose: boolean;
  canVote: boolean;
  currentUserId?: string;
  onChange: () => void;
  onMessage: (msg: string) => void;
  onError: (msg: string) => void;
}

function ProposalsSection({
  lexeme,
  proposals,
  canPropose,
  canVote,
  currentUserId,
  onChange,
  onMessage,
  onError,
}: ProposalsSectionProps) {
  const { t } = useTranslation();
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const current = lexeme.recommendation ?? 'neutral';
  const choices = LEXEME_RECOMMENDATIONS.filter((r) => r !== current);
  const [recommendation, setRecommendation] = useState<LexemeRecommendation>(choices[0]);
  const [note, setNote] = useState('');
  const [rationale, setRationale] = useState('');
  const [comment, setComment] = useState('');

  const open = proposals.find((p) => p.status === 'open');
  const history = proposals.filter((p) => p.status !== 'open');
  const myVote = open?.votes.find((v) => v.user_id === currentUserId);

  const run = async (action: () => Promise<unknown>, message: string) => {
    setBusy(true);
    try {
      await action();
      onMessage(message);
      onChange();
    } catch (err: any) {
      onError(err.response?.data?.detail || t('word_detail.proposal_failed'));
    } finally {
      setBusy(false);
    }
  };

  const submitProposal = () =>
    run(async () => {
      await proposalService.proposeRecommendation(lexeme.id, {
        recommendation,
        ...(note.trim() && { note: note.trim() }),
        ...(rationale.trim() && { rationale: rationale.trim() }),
      });
      setShowForm(false);
      setNote('');
      setRationale('');
    }, t('word_detail.proposal_created'));

  const castVote = (choice: VoteChoice) =>
    run(async () => {
      await proposalService.vote(open!.id, choice, comment.trim() || undefined);
      setComment('');
    }, t('word_detail.vote_recorded'));

  const proposalTitle = (p: ChangeProposal) =>
    t('word_detail.proposal_title', {
      recommendation: t(`word_detail.recommendation_${p.payload.recommendation}`),
    });

  return (
    <section className="word-detail-section" id="proposals">
      <div className="word-detail-section-header">
        <h2>{t('word_detail.recommendation_heading')}</h2>
        {canPropose && !open && !showForm && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setRecommendation(choices[0]);
              setShowForm(true);
            }}
          >
            {t('word_detail.propose_change')}
          </button>
        )}
      </div>
      <p className="muted proposal-explainer">{t('word_detail.recommendation_explainer')}</p>

      {showForm && (
        <div className="form-editor">
          <div className="form-editor-row">
            <label>
              {t('word_detail.proposal_mark_as')}
              <select
                value={recommendation}
                onChange={(e) => setRecommendation(e.target.value as LexemeRecommendation)}
              >
                {choices.map((r) => (
                  <option key={r} value={r}>{t(`word_detail.recommendation_${r}`)}</option>
                ))}
              </select>
            </label>
          </div>
          <label className="form-editor-notes">
            {t('word_detail.proposal_note_label')}
            <input
              type="text"
              value={note}
              maxLength={1000}
              onChange={(e) => setNote(e.target.value)}
              placeholder={t('word_detail.proposal_note_placeholder')}
            />
          </label>
          <label className="form-editor-notes">
            {t('word_detail.proposal_rationale_label')}
            <textarea
              value={rationale}
              maxLength={2000}
              rows={3}
              onChange={(e) => setRationale(e.target.value)}
              placeholder={t('word_detail.proposal_rationale_placeholder')}
            />
          </label>
          <div className="form-editor-actions">
            <button type="button" className="btn btn-accent" onClick={submitProposal} disabled={busy}>
              {t('word_detail.proposal_submit')}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setShowForm(false)}
              disabled={busy}
            >
              {t('word_detail.cancel')}
            </button>
          </div>
        </div>
      )}

      {open && (
        <div className="proposal-card">
          <div className="proposal-card-head">
            <strong>{proposalTitle(open)}</strong>
            <span className="muted">
              {t('word_detail.proposal_by', {
                username: open.created_by_username ?? '?',
                date: new Date(open.created_at).toLocaleDateString(),
              })}
            </span>
          </div>
          {open.payload.note && (
            <p className="proposal-note">
              {t('word_detail.proposal_note_label')}: {open.payload.note}
            </p>
          )}
          {open.rationale && <blockquote className="proposal-rationale">{open.rationale}</blockquote>}

          <div className="proposal-tally">
            <span className="tally-approve">
              {t('word_detail.tally_approvals', { count: open.approvals, threshold: open.threshold })}
            </span>
            <span className={open.rejections > 0 ? 'tally-reject' : 'muted'}>
              {t('word_detail.tally_objections', { count: open.rejections })}
            </span>
          </div>
          {open.rejections > 0 && (
            <p className="muted proposal-blocked">{t('word_detail.proposal_blocked')}</p>
          )}

          {open.usage.length > 0 && (
            <div className="usage-table-wrap">
              <table className="usage-table">
                <caption>{t('word_detail.usage_caption')}</caption>
                <thead>
                  <tr>
                    <th>{t('word_detail.usage_word')}</th>
                    <th>{t('add_word.origin_label')}</th>
                    <th>{t('word_detail.usage_texts')}</th>
                    <th>{t('word_detail.usage_recordings')}</th>
                    <th>{t('word_detail.usage_places')}</th>
                  </tr>
                </thead>
                <tbody>
                  {open.usage.map((u) => (
                    <tr key={u.lexeme_id} className={u.lexeme_id === lexeme.id ? 'usage-self' : ''}>
                      <td>
                        {u.lexeme_id === lexeme.id ? (
                          u.lemma
                        ) : (
                          <Link to={`/words/${u.lexeme_id}`}>{u.lemma}</Link>
                        )}
                        {u.recommendation === 'preferred' && ' ★'}
                      </td>
                      <td>{u.origin ? t(`add_word.origin_${u.origin}`) : '—'}</td>
                      <td>{u.text_count}</td>
                      <td>{u.audio_count}</td>
                      <td>{u.locations.length ? u.locations.join(', ') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <VoteList proposal={open} />

          {(canVote || open.created_by_id === currentUserId) && (
            <div className="proposal-actions">
              {canVote && (
                <>
                  <input
                    type="text"
                    value={comment}
                    maxLength={1000}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder={t('word_detail.vote_comment_placeholder')}
                  />
                  <button
                    type="button"
                    className={`btn ${myVote?.choice === 'approve' ? 'btn-accent' : 'btn-ghost'}`}
                    onClick={() => castVote('approve')}
                    disabled={busy}
                  >
                    ✓ {t('word_detail.vote_approve')}
                  </button>
                  <button
                    type="button"
                    className={`btn btn-ghost ${myVote?.choice === 'reject' ? 'vote-selected-reject' : ''}`}
                    onClick={() => castVote('reject')}
                    disabled={busy}
                  >
                    ✗ {t('word_detail.vote_reject')}
                  </button>
                </>
              )}
              {open.created_by_id === currentUserId && (
                <button
                  type="button"
                  className="btn btn-ghost btn-xs"
                  onClick={() =>
                    run(() => proposalService.withdraw(open.id), t('word_detail.proposal_withdrawn'))
                  }
                  disabled={busy}
                >
                  {t('word_detail.proposal_withdraw')}
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {!open && !showForm && history.length === 0 && (
        <p className="muted">{t('word_detail.no_proposals')}</p>
      )}

      {history.length > 0 && (
        <ul className="proposal-history">
          {history.map((p) => (
            <li key={p.id}>
              <details>
                <summary>
                  <span className={`proposal-status proposal-status-${p.status}`}>
                    {t(`word_detail.proposal_status_${p.status}`)}
                  </span>{' '}
                  {proposalTitle(p)}
                  <span className="muted">
                    {' · '}
                    {t('word_detail.tally_short', {
                      approvals: p.approvals,
                      rejections: p.rejections,
                    })}
                    {' · '}
                    {new Date(p.resolved_at ?? p.created_at).toLocaleDateString()}
                  </span>
                </summary>
                {p.rationale && <blockquote className="proposal-rationale">{p.rationale}</blockquote>}
                <VoteList proposal={p} />
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function VoteList({ proposal }: { proposal: ChangeProposal }) {
  const { t } = useTranslation();
  return (
    <ul className="vote-list">
      {proposal.votes.map((v) => (
        <li key={v.user_id} className={`vote vote-${v.choice}`}>
          <span className="vote-choice">
            {v.choice === 'approve' ? '✓' : '✗'}{' '}
            {t(v.choice === 'approve' ? 'word_detail.vote_approve' : 'word_detail.vote_reject')}
          </span>
          <span className="vote-user">{v.username ?? '?'}</span>
          {v.comment && <span className="vote-comment">“{v.comment}”</span>}
        </li>
      ))}
    </ul>
  );
}
