import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import authService from '../services/authService';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

type Status = 'working' | 'verified' | 'failed' | 'no-token';

/**
 * Landing page for the emailed verification link. With a token it verifies
 * immediately; without one it shows the signed-in user's verification
 * status with a resend button.
 */
export default function VerifyEmail() {
  const { t } = useTranslation();
  const { user, isAuthenticated } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [status, setStatus] = useState<Status>(token ? 'working' : 'no-token');
  const [error, setError] = useState('');
  const [resent, setResent] = useState(false);
  const attempted = useRef(false);

  useEffect(() => {
    if (!token || attempted.current) return;
    attempted.current = true;
    authService
      .verifyEmail(token)
      .then(() => setStatus('verified'))
      .catch((err) => {
        setError(err.response?.data?.detail || t('auth.verify_failed'));
        setStatus('failed');
      });
  }, [token, t]);

  const resend = async () => {
    try {
      await authService.requestVerification();
      setResent(true);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.verify_failed'));
    }
  };

  const alreadyVerified = isAuthenticated && !!user?.email_verified_at;

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-logo">Nativo<b>.</b></h1>
          <h2 className="login-title">{t('auth.verify_title')}</h2>
        </div>

        <div className="login-form">
          {status === 'working' && <p>{t('auth.verify_working')}</p>}
          {status === 'verified' && (
            <p className="auth-flow-success">{t('auth.verify_done')}</p>
          )}
          {status === 'failed' && <div className="error-message">{error}</div>}
          {status === 'no-token' &&
            (alreadyVerified ? (
              <p className="auth-flow-success">{t('auth.verify_already')}</p>
            ) : isAuthenticated ? (
              <>
                <p>{t('auth.verify_prompt')}</p>
                {resent ? (
                  <p className="auth-flow-success">{t('auth.verify_resent')}</p>
                ) : (
                  <button type="button" className="login-button" onClick={() => void resend()}>
                    {t('auth.verify_resend')}
                  </button>
                )}
                {error && <div className="error-message">{error}</div>}
              </>
            ) : (
              <p>{t('auth.reset_missing_token')}</p>
            ))}
          {status === 'failed' && isAuthenticated && !alreadyVerified && (
            <button type="button" className="login-button" onClick={() => void resend()}>
              {t('auth.verify_resend')}
            </button>
          )}
        </div>

        <div className="login-footer">
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
