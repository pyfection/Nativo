import { useState } from 'react';
import { Link } from 'react-router-dom';
import authService from '../services/authService';
import './PasswordResetRequest.css';

export default function PasswordResetRequest() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    // Validate email format (basic validation)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      setError('Please enter a valid email address');
      setLoading(false);
      return;
    }

    try {
      await authService.requestPasswordReset(email);
      setSuccess(true);
      setEmail(''); // Clear email for security
    } catch (err: any) {
      // Handle different error types
      if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
        setError('Network error. Please check your connection and try again.');
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Request timed out. Please check your connection and try again.');
      } else if (err.response?.status === 422) {
        setError('Please enter a valid email address.');
      } else if (err.response?.status >= 500) {
        setError('Server error. Please try again in a few moments.');
      } else {
        // Even on error, show success message for security (prevents email enumeration)
        setSuccess(true);
        setEmail('');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setError(''); // Clear error when user types
  };

  return (
    <div className="password-reset-request-page">
      <div className="password-reset-request-container">
        <div className="password-reset-request-header">
          <h1 className="password-reset-request-logo">Nativo</h1>
          <h2 className="password-reset-request-title">Reset Your Password</h2>
          <p className="password-reset-request-subtitle">
            Enter your email address and we'll send you a link to reset your password
          </p>
        </div>

        {success ? (
          <div className="password-reset-request-success">
            <div className="success-icon">✓</div>
            <h3>Check Your Email</h3>
            <p>
              If an account with that email exists, a password reset link has been sent.
              Please check your inbox and follow the instructions.
            </p>
            <p className="success-note">
              Didn't receive an email? Check your spam folder or try again in a few minutes.
            </p>
            <Link to="/login" className="back-to-login-link">
              Back to Login
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="password-reset-request-form">
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={email}
                onChange={handleChange}
                required
                autoComplete="email"
                placeholder="your.email@example.com"
                disabled={loading}
              />
            </div>

            <button type="submit" className="password-reset-request-button" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <div className="password-reset-request-footer">
          <p>
            Remember your password?{' '}
            <Link to="/login" className="login-link">
              Sign in here
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
