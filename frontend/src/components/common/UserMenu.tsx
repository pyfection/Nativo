import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { API_URL } from '../../services/api';
import './UserMenu.css';

export default function UserMenu() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/');
  };

  const handleAdminClick = () => {
    // Open backend admin interface in new tab
    window.open(`${API_URL}/admin`, '_blank', 'noopener,noreferrer');
  };

  if (!isAuthenticated) {
    return (
      <div className="user-menu-guest">
        <Link to="/login" className="login-btn">
          Sign In
        </Link>
        <Link to="/register" className="register-btn">
          Register
        </Link>
      </div>
    );
  }

  return (
    <div className="user-menu" ref={menuRef}>
      <button className="user-menu-button" onClick={() => setIsOpen(!isOpen)}>
        <div className="user-avatar">
          {user?.username.charAt(0).toUpperCase()}
        </div>
        <span className="user-name">{user?.username}</span>
        <svg
          className={`chevron ${isOpen ? 'open' : ''}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="currentColor"
        >
          <path d="M6 9L1 4h10z" />
        </svg>
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <div className="user-info">
              <div className="user-info-name">{user?.username}</div>
              <div className="user-info-email">{user?.email}</div>
              <div className="user-info-role">{user?.role}</div>
            </div>
          </div>
          <div className="user-menu-divider" />
          <div className="user-menu-items">
            {isAdmin && (
              <button onClick={handleAdminClick} className="user-menu-item admin">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 1a2 2 0 0 1 2 2v1h3.5a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5H13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6h-.5a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5H6V3a2 2 0 0 1 2-2h0zm1 3V3a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v1h2z"/>
                  <path d="M3 6v6a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V6H3z"/>
                </svg>
                Admin Panel
              </button>
            )}
            <button onClick={handleLogout} className="user-menu-item logout">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M5 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H5zm6 13H5V2h6v12z"/>
                <path d="M10 8a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1 0-1h3A.5.5 0 0 1 10 8z"/>
              </svg>
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

