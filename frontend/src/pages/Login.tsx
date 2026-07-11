import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

export default function Login() {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  // Land back on the page the visitor came from (ProtectedRoute and the
  // guest CTAs pass it via state) instead of dumping everyone on the home page.
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(formData);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.login_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-logo">Nativo<b>.</b></h1>
          <h2 className="login-title">{t('auth.welcome_back')}</h2>
          <p className="login-subtitle">{t('auth.sign_in_subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="username">{t('auth.email_or_username_label')}</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete="username"
              placeholder={t('auth.email_or_username_placeholder')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('auth.password_label')}</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
              placeholder={t('auth.password_placeholder')}
              minLength={8}
            />
          </div>

          <Link to="/forgot-password" className="forgot-password-link">
            {t('auth.forgot_link')}
          </Link>

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? t('auth.signing_in') : t('auth.sign_in')}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {t('auth.no_account_pre')}{' '}
            <Link to="/register" state={location.state} className="register-link">
              {t('auth.register_link')}
            </Link>
          </p>
          <p>
            <Link to="/" className="home-link">
              {t('auth.back_to_home')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
