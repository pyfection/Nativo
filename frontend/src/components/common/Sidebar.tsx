import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import './Sidebar.css';

interface NavItem {
  path: string;
  label: string;
  icon: JSX.Element;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/words',
    label: 'Words',
    icon: (
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M4 7l3.2 10L12 7l4.8 10L20 7" />
      </svg>
    ),
  },
  {
    path: '/dictionary',
    label: 'Dictionary',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811V2.828zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492V2.687zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783z" />
      </svg>
    ),
  },
  {
    path: '/documents',
    label: 'Documents',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M5 0h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2z" />
        <path d="M6 3h6v1H6V3zm0 2h6v1H6V5zm0 2h6v1H6V7zm0 2h4v1H6V9z" fill="white" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);

  const isActive = (path: string) => location.pathname.startsWith(path);

  const handleToggle = () => {
    setIsExpanded((prev) => !prev);
  };

  return (
    <aside className={`sidebar ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="sidebar-toggle">
        <button
          type="button"
          className="sidebar-toggle-button"
          onClick={handleToggle}
          aria-pressed={isExpanded}
          aria-label={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
          title={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <span className={`toggle-icon ${isExpanded ? 'open' : ''}`} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M5.5 3.5a.5.5 0 0 1 .832-.374l4 3.5a.5.5 0 0 1 0 .748l-4 3.5A.5.5 0 0 1 5 10.5v-7a.5.5 0 0 1 .5-.5z" />
            </svg>
          </span>
          {isExpanded && <span className="toggle-label">Hide menu</span>}
        </button>
      </div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-button ${isActive(item.path) ? 'active' : ''}`}
            title={item.label}
            aria-label={item.label}
          >
            {item.icon}
            {isExpanded && <span className="sidebar-label">{item.label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

