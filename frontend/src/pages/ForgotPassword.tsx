import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import authService from '../services/authService';
import './Login.css';

export default function ForgotPassword() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.forgot_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-logo">Nativo<b>.</b></h1>
          <h2 className="login-title">{t('auth.forgot_title')}</h2>
          <p className="login-subtitle">{t('auth.forgot_subtitle')}</p>
        </div>

        {sent ? (
          <div className="login-form">
            <p className="auth-flow-success">{t('auth.forgot_sent')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}
            <div className="form-group">
              <label htmlFor="email">{t('auth.email_label')}</label>
              <input
                type="email"
                id="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder={t('auth.email_placeholder')}
              />
            </div>
            <button type="submit" className="login-button" disabled={loading}>
              {loading ? t('auth.forgot_sending') : t('auth.forgot_send')}
            </button>
          </form>
        )}

        <div className="login-footer">
          <p>
            <Link to="/login" className="register-link">
              {t('auth.back_to_sign_in')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
