import { useTranslation } from 'react-i18next';

import { dismissFailures, flush, useOutbox } from '../../services/outbox';
import './OfflineBanner.css';

/**
 * Connection status under the header: offline notice, changes waiting to be
 * sent (see services/outbox.ts), and saved changes the server refused.
 */
export default function OfflineBanner() {
  const { t } = useTranslation();
  const { online, pending, sending, failures } = useOutbox();

  if (online && pending === 0 && failures.length === 0) return null;

  return (
    <div className="offline-banner" role="status" aria-live="polite">
      {!online && (
        <p>
          <strong>{t('offline.offline')}</strong> {t('offline.offline_body')}
          {pending > 0 && ` ${t('offline.waiting', { count: pending })}`}
        </p>
      )}
      {online && pending > 0 && (
        <p>
          {sending ? t('offline.sending', { count: pending }) : t('offline.waiting', { count: pending })}
          {!sending && (
            <button type="button" className="offline-banner-action" onClick={() => void flush()}>
              {t('offline.send_now')}
            </button>
          )}
        </p>
      )}
      {failures.length > 0 && (
        <div className="offline-banner-failures">
          <p>
            {t('offline.failed', { count: failures.length })}
            <button type="button" className="offline-banner-action" onClick={dismissFailures}>
              {t('offline.dismiss')}
            </button>
          </p>
          <ul>
            {failures.map((failure, i) => (
              <li key={i}>
                {failure.label} — {failure.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
