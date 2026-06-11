import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import { AudioListItem, listAudio } from '../services/audioService';
import './AudioList.css';

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
        <h1>{t('audio_page.title', { language: selectedLanguage.name })}</h1>
        <p className="audio-list-subtitle">{t('audio_page.subtitle')}</p>
      </header>

      {loading && <p className="audio-list-status">{t('audio_page.loading')}</p>}
      {error && <p className="audio-list-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="audio-list-empty">
          <p>{t('audio_page.empty_title')}</p>
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
