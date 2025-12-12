import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import authService from '../services/authService';
import './PasswordReset.css';

export default function PasswordReset() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  });
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Get token from URL query parameter
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      setError('Invalid reset link. Please request a new password reset.');
    } else {
      setToken(tokenParam);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!token) {
      setError('Invalid reset link. Please request a new password reset.');
      return;
    }

    setLoading(true);

    try {
      await authService.resetPassword(token, formData.password);
      setSuccess(true);
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      // Handle different error types
      if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
        setError('Network error. Please check your connection and try again.');
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Request timed out. Please check your connection and try again.');
      } else if (err.response?.status === 400) {
        const errorDetail = err.response?.data?.detail || 'Invalid or expired reset token';
        if (errorDetail.includes('expired')) {
          setError('This reset link has expired. Please request a new password reset.');
        } else if (errorDetail.includes('Invalid')) {
          setError('Invalid reset link. Please check your email and try again, or request a new reset link.');
        } else if (errorDetail.includes('inactive')) {
          setError('Your account is inactive. Please contact support for assistance.');
        } else {
          setError(errorDetail);
        }
      } else if (err.response?.status === 403) {
        setError('Your account is inactive. Please contact support for assistance.');
      } else if (err.response?.status === 422) {
        setError('Password must be at least 8 characters long.');
      } else if (err.response?.status === 503) {
        setError('Service temporarily unavailable. Please try again in a few moments.');
      } else if (err.response?.status >= 500) {
        setError('Server error. Please try again later. If the problem persists, contact support.');
      } else {
        setError(err.response?.data?.detail || 'Failed to reset password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError(''); // Clear error when user types
  };

  if (success) {
    return (
      <div className="password-reset-page">
        <div className="password-reset-container">
          <div className="password-reset-success">
            <div className="success-icon">✓</div>
            <h2>Password Reset Successful</h2>
            <p>Your password has been reset successfully. You can now log in with your new password.</p>
            <p className="redirect-note">Redirecting to login page...</p>
            <Link to="/login" className="login-link-button">
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="password-reset-page">
      <div className="password-reset-container">
        <div className="password-reset-header">
          <h1 className="password-reset-logo">Nativo</h1>
          <h2 className="password-reset-title">Set New Password</h2>
          <p className="password-reset-subtitle">
            Enter your new password below
          </p>
        </div>

        <form onSubmit={handleSubmit} className="password-reset-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="password">New Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              autoComplete="new-password"
              placeholder="Enter new password (min 8 characters)"
              minLength={8}
              disabled={loading || !token}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              autoComplete="new-password"
              placeholder="Confirm your new password"
              minLength={8}
              disabled={loading || !token}
            />
          </div>

          <button 
            type="submit" 
            className="password-reset-button" 
            disabled={loading || !token}
          >
            {loading ? 'Resetting Password...' : 'Reset Password'}
          </button>
        </form>

        {!token && (
          <div className="password-reset-footer">
            <p>
              Need a new reset link?{' '}
              <Link to="/password-reset-request" className="reset-link">
                Request Password Reset
              </Link>
            </p>
          </div>
        )}

        <div className="password-reset-footer">
          <p>
            <Link to="/login" className="login-link">
              Back to Login
            </Link>
          </p>
          <p>
            <Link to="/" className="home-link">
              ← Back to Home
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
