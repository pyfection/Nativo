import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import './Register.css';

export default function Register() {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  // Land back where the visitor's intent was (e.g. the word list they were
  // reading when they clicked "create an account").
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError(t('auth.passwords_no_match'));
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setError(t('auth.password_min_length', { n: 8 }));
      return;
    }

    setLoading(true);

    try {
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
      });
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.registration_failed'));
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
    <div className="register-page">
      <div className="register-container">
        <div className="register-header">
          <h1 className="register-logo">Nativo<b>.</b></h1>
          <h2 className="register-title">{t('auth.join_community_title')}</h2>
          <p className="register-subtitle">{t('auth.register_subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="register-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">{t('auth.email_label')}</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              autoComplete="email"
              placeholder={t('auth.email_placeholder')}
            />
          </div>

          <div className="form-group">
            <label htmlFor="username">{t('auth.username_label')}</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete="username"
              placeholder={t('auth.username_placeholder')}
              minLength={3}
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
              autoComplete="new-password"
              placeholder={t('auth.create_password_placeholder', { n: 8 })}
              minLength={8}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">{t('auth.confirm_password_label')}</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              autoComplete="new-password"
              placeholder={t('auth.confirm_password_placeholder')}
              minLength={8}
            />
          </div>

          <button type="submit" className="register-button" disabled={loading}>
            {loading ? t('auth.creating_account') : t('auth.create_account')}
          </button>
        </form>

        <div className="register-footer">
          <p>
            {t('auth.have_account_pre')}{' '}
            <Link to="/login" state={location.state} className="login-link">
              {t('auth.sign_in_link')}
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
