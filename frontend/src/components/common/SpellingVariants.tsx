import { useEffect, useState } from 'react';

import wordService, { SpellingVariant } from '../../services/wordService';
import './SpellingVariants.css';

interface SpellingVariantsProps {
  /** WordForm whose non-standard spellings these are. */
  wordFormId: string;
  /** True if the current user can add/remove variants on this form. */
  canEdit: boolean;
  /** Surface success messages to the parent toast stack. */
  onMessage?: (msg: string) => void;
  /** Surface errors similarly. */
  onError?: (msg: string) => void;
}

/**
 * Per-WordForm spelling-variant editor.
 *
 * The WordForm's own `form` is the standard spelling; this lists the
 * alternative, non-standard ways the same form gets written (languages without
 * a settled orthography). Each variant is a removable chip; contributors can
 * add one inline with an optional provenance note.
 *
 * Mirrors AudioRecorder: self-contained, keyed on wordFormId, talks straight to
 * the service, and reports outcomes up through onMessage/onError.
 */
export default function SpellingVariants({
  wordFormId,
  canEdit,
  onMessage,
  onError,
}: SpellingVariantsProps) {
  const [variants, setVariants] = useState<SpellingVariant[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [variantDraft, setVariantDraft] = useState('');
  const [noteDraft, setNoteDraft] = useState('');
  const [busy, setBusy] = useState(false);

  // Load + reset whenever the form changes.
  useEffect(() => {
    let cancelled = false;
    setVariants([]);
    wordService
      .listSpellings(wordFormId)
      .then((data) => {
        if (!cancelled) setVariants(data);
      })
      .catch(() => {
        // A form with no variants is the common case, not an error.
        if (!cancelled) setVariants([]);
      });
    return () => {
      cancelled = true;
    };
  }, [wordFormId]);

  const resetAdd = () => {
    setShowAdd(false);
    setVariantDraft('');
    setNoteDraft('');
  };

  const handleAdd = async () => {
    const variant = variantDraft.trim();
    if (!variant) return;
    setBusy(true);
    try {
      const created = await wordService.addSpelling(wordFormId, {
        variant,
        ...(noteDraft.trim() && { note: noteDraft.trim() }),
      });
      setVariants((prev) =>
        [...prev, created].sort((a, b) => a.variant.localeCompare(b.variant)),
      );
      resetAdd();
      onMessage?.('Spelling variant added.');
    } catch (err: any) {
      onError?.(err.response?.data?.detail || 'Failed to add spelling variant.');
    } finally {
      setBusy(false);
    }
  };

  const handleRemove = async (variant: SpellingVariant) => {
    if (!window.confirm(`Remove the spelling "${variant.variant}"?`)) return;
    setBusy(true);
    try {
      await wordService.removeSpelling(variant.id);
      setVariants((prev) => prev.filter((v) => v.id !== variant.id));
      onMessage?.('Spelling variant removed.');
    } catch (err: any) {
      onError?.(err.response?.data?.detail || 'Failed to remove spelling variant.');
    } finally {
      setBusy(false);
    }
  };

  // Nothing to show and nothing to add: render nothing so empty forms stay tidy.
  if (variants.length === 0 && !canEdit) return null;

  return (
    <div className="spelling-variants">
      <div className="spelling-variants-head">
        <span className="spelling-variants-label" title="Other ways this form is written outside the standard orthography.">
          Also written
        </span>
        {variants.length === 0 && <span className="spelling-variants-empty">—</span>}
        {variants.map((variant) => (
          <span key={variant.id} className="spelling-chip" title={variant.note || undefined}>
            {variant.variant}
            {canEdit && (
              <button
                type="button"
                className="spelling-chip-remove"
                onClick={() => handleRemove(variant)}
                disabled={busy}
                aria-label={`Remove spelling ${variant.variant}`}
                title="Remove this spelling"
              >
                ✕
              </button>
            )}
          </span>
        ))}
        {canEdit && !showAdd && (
          <button
            type="button"
            className="btn btn-ghost btn-xs"
            onClick={() => setShowAdd(true)}
            title="Record another way this form is written."
          >
            + add spelling
          </button>
        )}
      </div>

      {canEdit && showAdd && (
        <div className="spelling-variants-add">
          <input
            type="text"
            className="spelling-variants-input"
            placeholder="e.g. eich"
            value={variantDraft}
            autoFocus
            onChange={(e) => setVariantDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd();
              if (e.key === 'Escape') resetAdd();
            }}
          />
          <input
            type="text"
            className="spelling-variants-input spelling-variants-note"
            placeholder="note (optional) — e.g. older spelling"
            value={noteDraft}
            onChange={(e) => setNoteDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAdd();
              if (e.key === 'Escape') resetAdd();
            }}
          />
          <button
            type="button"
            className="btn btn-accent btn-xs"
            onClick={handleAdd}
            disabled={busy || !variantDraft.trim()}
          >
            Add
          </button>
          <button type="button" className="btn btn-ghost btn-xs" onClick={resetAdd} disabled={busy}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
