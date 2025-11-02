import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

export default function Sidebar() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {/* Words Section */}
        <div className="sidebar-section">
          <h3 className="sidebar-section-title">Words</h3>
          <div className="sidebar-buttons">
            <Link
              to="/words/add"
              className={`sidebar-button ${isActive('/words/add') ? 'active' : ''}`}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
              </svg>
              Add Word
            </Link>
            <Link
              to="/words"
              className={`sidebar-button ${isActive('/words') && !isActive('/words/add') ? 'active' : ''}`}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h3A1.5 1.5 0 0 1 7 2.5v3A1.5 1.5 0 0 1 5.5 7h-3A1.5 1.5 0 0 1 1 5.5v-3zm8 0A1.5 1.5 0 0 1 10.5 1h3A1.5 1.5 0 0 1 15 2.5v3A1.5 1.5 0 0 1 13.5 7h-3A1.5 1.5 0 0 1 9 5.5v-3zm-8 8A1.5 1.5 0 0 1 2.5 9h3A1.5 1.5 0 0 1 7 10.5v3A1.5 1.5 0 0 1 5.5 15h-3A1.5 1.5 0 0 1 1 13.5v-3zm8 0A1.5 1.5 0 0 1 10.5 9h3a1.5 1.5 0 0 1 1.5 1.5v3a1.5 1.5 0 0 1-1.5 1.5h-3A1.5 1.5 0 0 1 9 13.5v-3z"/>
              </svg>
              View Words
            </Link>
          </div>
        </div>

        {/* Documents Section */}
        <div className="sidebar-section">
          <h3 className="sidebar-section-title">Documents</h3>
          <div className="sidebar-buttons">
            <Link
              to="/documents/add"
              className={`sidebar-button ${isActive('/documents/add') ? 'active' : ''}`}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2z"/>
              </svg>
              Add Document
            </Link>
            <Link
              to="/documents"
              className={`sidebar-button ${isActive('/documents') && !isActive('/documents/add') ? 'active' : ''}`}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M5 0h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2z"/>
                <path d="M6 3h6v1H6V3zm0 2h6v1H6V5zm0 2h6v1H6V7zm0 2h4v1H6V9z" fill="white"/>
              </svg>
              View Documents
            </Link>
          </div>
        </div>
      </nav>
    </aside>
  );
}

