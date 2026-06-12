import { useEffect, useRef, useState, ReactNode } from 'react';
import './Dropdown.css';

export interface DropdownOption<T = string> {
  /** Unique key for the option. */
  value: T;
  /** Visible label. */
  label: string;
  /** Optional secondary text shown beneath the label (e.g. native name). */
  hint?: string;
  /** If true, render a non-selectable separator after this option. */
  separatorAfter?: boolean;
}

interface DropdownProps<T> {
  /** Currently selected value. */
  value: T;
  options: DropdownOption<T>[];
  onChange: (value: T) => void;
  /** Optional label shown to the LEFT of the trigger. */
  label?: string;
  /** Accessible name for the trigger button. */
  ariaLabel?: string;
  /** Optional content rendered inside the trigger before the selected label. */
  triggerPrefix?: ReactNode;
  /** Optional alignment of the popover relative to the trigger. */
  align?: 'left' | 'right';
  /** Optional CSS class on the wrapper. */
  className?: string;
  /** Optional min-width for the trigger button. */
  minWidth?: number;
}

/**
 * Dark-themed custom dropdown. Replaces native <select> in places where
 * we need the popover to fit the new design (Chrome/Safari ignore CSS on
 * <option>, so a styled native select can't match the rest of the page).
 */
export default function Dropdown<T extends string>({
  value,
  options,
  onChange,
  label,
  ariaLabel,
  triggerPrefix,
  align = 'left',
  className,
  minWidth,
}: DropdownProps<T>) {
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState<number>(-1);
  const wrapRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        triggerRef.current?.focus();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIdx((i) => Math.min(options.length - 1, i + 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIdx((i) => Math.max(0, i - 1));
      } else if (e.key === 'Enter' && activeIdx >= 0) {
        e.preventDefault();
        onChange(options[activeIdx].value);
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open, options, onChange, activeIdx]);

  useEffect(() => {
    if (open) {
      const idx = options.findIndex((o) => o.value === value);
      setActiveIdx(idx >= 0 ? idx : 0);
    }
  }, [open, options, value]);

  return (
    <div ref={wrapRef} className={`dropdown ${className ?? ''}`}>
      {label && (
        <label className="dropdown-label" onClick={() => triggerRef.current?.focus()}>
          {label}
        </label>
      )}
      <button
        ref={triggerRef}
        type="button"
        className={`dropdown-trigger ${open ? 'open' : ''}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel ?? selected?.label}
        onClick={() => setOpen((v) => !v)}
        style={minWidth ? { minWidth } : undefined}
      >
        {triggerPrefix}
        <span className="dropdown-trigger-label">
          {selected?.label ?? '—'}
        </span>
        <svg className="dropdown-caret" width="10" height="10" viewBox="0 0 12 12" aria-hidden>
          <path fill="currentColor" d="M6 8.5 1.5 4h9z" />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          className={`dropdown-menu dropdown-menu-${align}`}
          tabIndex={-1}
        >
          {options.map((opt, i) => (
            <li key={String(opt.value)}>
              <button
                type="button"
                role="option"
                aria-selected={opt.value === value}
                className={`dropdown-option ${i === activeIdx ? 'active' : ''} ${
                  opt.value === value ? 'selected' : ''
                }`}
                onMouseEnter={() => setActiveIdx(i)}
                onClick={() => {
                  onChange(opt.value);
                  setOpen(false);
                  triggerRef.current?.focus();
                }}
              >
                <span className="dropdown-option-label">{opt.label}</span>
                {opt.hint && (
                  <span className="dropdown-option-hint">{opt.hint}</span>
                )}
              </button>
              {opt.separatorAfter && <hr className="dropdown-separator" aria-hidden />}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
