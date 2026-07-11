import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../../App';
import { ActivityItem, getActivity } from '../../services/activityService';
import { languageDisplayName } from '../../utils/languageName';
import './RecentActivity.css';

interface RecentActivityProps {
  selectedLanguage: Language;
}

const ICON_BY_TYPE: Record<ActivityItem['type'], string> = {
  word_added: '📝',
  text_added: '📚',
  contributor_joined: '🤝',
};

/** Feed entries deep-link to the thing that was added, so the feed doubles
 *  as a browsing entry point (especially for logged-out visitors). */
function entityHref(item: ActivityItem): string | null {
  if (!item.entity_id) return null;
  if (item.type === 'word_added') return `/words/${item.entity_id}`;
  if (item.type === 'text_added') return `/documents/${item.entity_id}`;
  return null;
}

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

  /** Compose the line in the interface language from the structured parts;
   *  fall back to the server's English summary for older payloads. */
  const itemLabel = (item: ActivityItem): string => {
    if (!item.subject) return item.summary;
    if (item.type === 'contributor_joined') {
      const level = item.detail ? t(`proficiency.${item.detail}`) : '';
      return t('activity.item_contributor_joined', { subject: item.subject, level });
    }
    return t(`activity.item_${item.type}`, { subject: item.subject });
  };
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
        {t('activity.heading', { language: languageDisplayName(selectedLanguage) })}
      </h3>

      {loading && <p className="recent-activity-loading">{t('activity.loading')}</p>}

      {error && <p className="recent-activity-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="recent-activity-empty">{t('activity.empty')}</p>
      )}

      {items.length > 0 && (
        <ul className="recent-activity-list">
          {items.map((item, index) => {
            const href = entityHref(item);
            return (
              <li key={`${item.type}-${index}-${item.timestamp}`} className="recent-activity-item">
                <span className="recent-activity-icon" aria-hidden="true">
                  {ICON_BY_TYPE[item.type]}
                </span>
                <div className="recent-activity-body">
                  <p className="recent-activity-summary">
                    {href ? (
                      <Link to={href} className="recent-activity-link">
                        {itemLabel(item)}
                      </Link>
                    ) : (
                      itemLabel(item)
                    )}
                  </p>
                  <p className="recent-activity-meta">
                    {item.actor && <span>{item.actor} · </span>}
                    <time dateTime={item.timestamp}>
                      {relativeTime(item.timestamp, i18n.language || 'en')}
                    </time>
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
