import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../../App';
import { ActivityItem, getActivity } from '../../services/activityService';
import './RecentActivity.css';

interface RecentActivityProps {
  selectedLanguage: Language;
}

const ICON_BY_TYPE: Record<ActivityItem['type'], string> = {
  word_added: '📝',
  text_added: '📚',
  contributor_joined: '🤝',
};

function relativeTime(timestamp: string, locale: string): string {
  const t = Date.parse(timestamp);
  if (Number.isNaN(t)) return timestamp;
  const diff = (t - Date.now()) / 1000;
  const abs = Math.abs(diff);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
  if (abs < 60) return rtf.format(Math.round(diff), 'second');
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute');
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), 'hour');
  if (abs < 2592000) return rtf.format(Math.round(diff / 86400), 'day');
  if (abs < 31536000) return rtf.format(Math.round(diff / 2592000), 'month');
  return rtf.format(Math.round(diff / 31536000), 'year');
}

export default function RecentActivity({ selectedLanguage }: RecentActivityProps) {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getActivity(selectedLanguage.id, 10)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load activity');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  return (
    <section className="recent-activity">
      <h3 className="recent-activity-heading">
        {t('activity.heading', { language: selectedLanguage.name })}
      </h3>

      {loading && <p className="recent-activity-loading">{t('activity.loading')}</p>}

      {error && <p className="recent-activity-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="recent-activity-empty">{t('activity.empty')}</p>
      )}

      {items.length > 0 && (
        <ul className="recent-activity-list">
          {items.map((item, index) => (
            <li key={`${item.type}-${index}-${item.timestamp}`} className="recent-activity-item">
              <span className="recent-activity-icon" aria-hidden="true">
                {ICON_BY_TYPE[item.type]}
              </span>
              <div className="recent-activity-body">
                <p className="recent-activity-summary">{item.summary}</p>
                <p className="recent-activity-meta">
                  {item.actor && <span>{item.actor} · </span>}
                  <time dateTime={item.timestamp}>
                    {relativeTime(item.timestamp, i18n.language || 'en')}
                  </time>
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
