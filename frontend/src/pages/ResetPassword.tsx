import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import authService from '../services/authService';
import './Login.css';

export default function ResetPassword() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError(t('auth.passwords_no_match'));
      return;
    }
    setLoading(true);
    try {
      await authService.resetPassword(token, password);
      setDone(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.reset_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-logo">Nativo<b>.</b></h1>
          <h2 className="login-title">{t('auth.reset_title')}</h2>
          {!done && <p className="login-subtitle">{t('auth.reset_subtitle')}</p>}
        </div>

        {!token ? (
          <div className="login-form">
            <div className="error-message">{t('auth.reset_missing_token')}</div>
          </div>
        ) : done ? (
          <div className="login-form">
            <p className="auth-flow-success">{t('auth.reset_done')}</p>
            <Link to="/login" className="login-button auth-flow-cta">
              {t('auth.sign_in')}
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}
            <div className="form-group">
              <label htmlFor="password">{t('auth.new_password_label')}</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                placeholder={t('auth.password_placeholder')}
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm">{t('auth.confirm_password_label')}</label>
              <input
                type="password"
                id="confirm"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
                placeholder={t('auth.password_placeholder')}
              />
            </div>
            <button type="submit" className="login-button" disabled={loading}>
              {loading ? t('auth.reset_saving') : t('auth.reset_save')}
            </button>
          </form>
        )}

        <div className="login-footer">
          <p>
            <Link to="/forgot-password" className="register-link">
              {t('auth.reset_request_new')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
