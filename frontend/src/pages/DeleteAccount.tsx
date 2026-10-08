import { FormEvent, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import authService from '../services/authService';
import { discardOutbox } from '../services/outbox';
import './DeleteAccount.css';

/**
 * Delete your own account (required by the app stores). Contributions stay
 * in the archive, credited to "deleted-user-…"; personal data is removed.
 */
export default function DeleteAccount() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [understood, setUnderstood] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await authService.deleteAccount(password);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('delete_account.failed'));
      setBusy(false);
      return;
    }
    await discardOutbox();
    window.alert(t('delete_account.done'));
    logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="delete-account-page">
      <h1>{t('delete_account.title')}</h1>
      <p>{t('delete_account.intro', { username: user?.username })}</p>

      <h2>{t('delete_account.removed_heading')}</h2>
      <ul>
        <li>{t('delete_account.removed_login')}</li>
        <li>{t('delete_account.removed_languages')}</li>
        <li>{t('delete_account.removed_learning')}</li>
        <li>{t('delete_account.removed_tokens')}</li>
      </ul>

      <h2>{t('delete_account.kept_heading')}</h2>
      <p>{t('delete_account.kept_body')}</p>
      <p>
        {t('delete_account.recordings_note')}{' '}
        <Link to="/privacy">{t('footer.privacy')}</Link>
      </p>

      <form className="delete-account-form" onSubmit={submit}>
        <label className="delete-account-field">
          <span>{t('delete_account.password')}</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        <label className="delete-account-check">
          <input
            type="checkbox"
            checked={understood}
            onChange={(e) => setUnderstood(e.target.checked)}
          />
          <span>{t('delete_account.confirm')}</span>
        </label>
        {error && <div className="error-message">{error}</div>}
        <button
          type="submit"
          className="delete-account-submit"
          disabled={busy || !password || !understood}
        >
          {busy ? t('delete_account.deleting') : t('delete_account.submit')}
        </button>
      </form>
    </div>
  );
}
