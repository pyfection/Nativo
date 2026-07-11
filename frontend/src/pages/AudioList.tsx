import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import { AudioListItem, listAudio } from '../services/audioService';
import './AudioList.css';
import { languageDisplayName } from '../utils/languageName';

interface AudioListProps {
  selectedLanguage: Language;
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '—';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function formatSize(bytes: number | null): string {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function AudioList({ selectedLanguage }: AudioListProps) {
  const { t } = useTranslation();
  const [items, setItems] = useState<AudioListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAudio(selectedLanguage.id)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load audio');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  return (
    <div className="audio-list-page">
      <header className="audio-list-header">
        <h1>{t('audio_page.title', { language: languageDisplayName(selectedLanguage) })}</h1>
        <p className="audio-list-subtitle">{t('audio_page.subtitle')}</p>
      </header>

      {loading && <p className="audio-list-status">{t('audio_page.loading')}</p>}
      {error && <p className="audio-list-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="audio-list-empty">
          <svg
            className="audio-list-empty-wave"
            viewBox="0 0 240 60"
            role="img"
            aria-label="Empty waveform placeholder"
          >
            {/* A flat-line "no audio" waveform with subtle bumps. */}
            <path
              d="M0 30 Q 20 28 40 30 T 80 30 T 120 30 T 160 30 T 200 30 T 240 30"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              opacity="0.4"
            />
            {[
              { x: 30, h: 6 },
              { x: 60, h: 10 },
              { x: 95, h: 4 },
              { x: 130, h: 8 },
              { x: 170, h: 5 },
              { x: 210, h: 9 },
            ].map((b, i) => (
              <line
                key={i}
                x1={b.x}
                x2={b.x}
                y1={30 - b.h}
                y2={30 + b.h}
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.5"
              />
            ))}
          </svg>
          <p className="audio-list-empty-title">{t('audio_page.empty_title')}</p>
          <p className="audio-list-empty-hint">{t('audio_page.empty_hint')}</p>
        </div>
      )}

      {items.length > 0 && (
        <ul className="audio-list">
          {items.map((a) => (
            <li key={a.id} className="audio-item">
              <div className="audio-item-meta">
                <span className="audio-item-icon" aria-hidden="true">🎙️</span>
                <div>
                  <div className="audio-item-filename">{a.file_path.split('/').pop()}</div>
                  <div className="audio-item-detail">
                    {formatDuration(a.duration)} · {formatSize(a.file_size)}
                    {a.uploader_username && ` · ${a.uploader_username}`}
                    {a.word_count > 0 && ` · ${a.word_count} ${t('audio_page.linked_words')}`}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
