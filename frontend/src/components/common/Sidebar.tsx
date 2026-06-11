import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './Sidebar.css';

interface NavItem {
  path: string;
  labelKey: string;
  icon: JSX.Element;
}

const NAV_ITEMS: NavItem[] = [
  {
    path: '/words',
    labelKey: 'nav.words',
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
    labelKey: 'nav.dictionary',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811V2.828zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492V2.687zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783z" />
      </svg>
    ),
  },
  {
    path: '/documents',
    labelKey: 'nav.documents',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M5 0h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2z" />
        <path d="M6 3h6v1H6V3zm0 2h6v1H6V5zm0 2h6v1H6V7zm0 2h4v1H6V9z" fill="white" />
      </svg>
    ),
  },
  {
    path: '/audio',
    labelKey: 'nav.audio',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3.5 4a.5.5 0 0 0-1 0v8a.5.5 0 0 0 1 0V4zm5 0a.5.5 0 0 0-1 0v8a.5.5 0 0 0 1 0V4zM6 6.5a.5.5 0 0 0-1 0v3a.5.5 0 0 0 1 0v-3zm-5 1a.5.5 0 0 0-1 0v1a.5.5 0 0 0 1 0v-1zm10-1a.5.5 0 0 0-1 0v3a.5.5 0 0 0 1 0v-3zM13.5 5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V5zm2.5 1.5a.5.5 0 0 0-1 0v3a.5.5 0 0 0 1 0v-3z" />
      </svg>
    ),
  },
  {
    path: '/contributors',
    labelKey: 'nav.contributors',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M15 14s1 0 1-1-1-4-5-4-5 3-5 4 1 1 1 1h8zm-7.978-1A.261.261 0 0 1 7 12.996c.001-.264.167-1.03.76-1.72C8.312 10.629 9.282 10 11 10c1.717 0 2.687.63 3.24 1.276.593.69.758 1.457.76 1.72l-.008.002a.274.274 0 0 1-.014.002H7.022zM11 7a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm3-2a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM6.936 9.28a5.88 5.88 0 0 0-1.23-.247A7.35 7.35 0 0 0 5 9c-4 0-5 3-5 4 0 .667.333 1 1 1h4.216A2.238 2.238 0 0 1 5 13c0-1.01.377-2.042 1.09-2.904.243-.294.526-.569.846-.816zM4.92 10A5.493 5.493 0 0 0 4 13H1c0-.26.164-1.03.76-1.724.545-.636 1.492-1.256 3.16-1.275zM1.5 5.5a3 3 0 1 1 6 0 3 3 0 0 1-6 0zm3-2a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
      </svg>
    ),
  },
  {
    path: '/languages',
    labelKey: 'nav.languages',
    icon: (
      <svg width="18" height="18" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm7.5-6.923c-.67.204-1.335.82-1.887 1.855A7.97 7.97 0 0 0 5.145 4H7.5V1.077zM4.09 4a9.267 9.267 0 0 1 .64-1.539 6.7 6.7 0 0 1 .597-.933A7.025 7.025 0 0 0 2.255 4H4.09zm-.582 3.5c.03-.877.138-1.718.312-2.5H1.674a6.958 6.958 0 0 0-.656 2.5h2.49zM4.847 5a12.5 12.5 0 0 0-.338 2.5H7.5V5H4.847zM8.5 5v2.5h2.99a12.495 12.495 0 0 0-.337-2.5H8.5zM4.51 8.5a12.5 12.5 0 0 0 .337 2.5H7.5V8.5H4.51zm3.99 0V11h2.653c.187-.765.306-1.608.338-2.5H8.5zM5.145 12c.138.386.295.744.468 1.068.552 1.035 1.218 1.65 1.887 1.855V12H5.145zm.182 2.472a6.696 6.696 0 0 1-.597-.933A9.268 9.268 0 0 1 4.09 12H2.255a7.024 7.024 0 0 0 3.072 2.472zM3.82 11a13.652 13.652 0 0 1-.312-2.5h-2.49c.062.89.291 1.733.656 2.5H3.82zm6.853 3.472A7.024 7.024 0 0 0 13.745 12H11.91a9.27 9.27 0 0 1-.64 1.539 6.688 6.688 0 0 1-.597.933zM8.5 12v2.923c.67-.204 1.335-.82 1.887-1.855.173-.324.33-.682.468-1.068H8.5zm3.68-1h2.146c.365-.767.594-1.61.656-2.5h-2.49a13.65 13.65 0 0 1-.312 2.5zm2.802-3.5a6.959 6.959 0 0 0-.656-2.5H12.18c.174.782.282 1.623.312 2.5h2.49zM11.27 2.461c.247.464.462.98.64 1.539h1.835a7.024 7.024 0 0 0-3.072-2.472c.218.284.418.598.597.933zM10.855 4a7.966 7.966 0 0 0-.468-1.068C9.835 1.897 9.17 1.282 8.5 1.077V4h2.355z" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const { t } = useTranslation();
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
        {NAV_ITEMS.map((item) => {
          const label = t(item.labelKey);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`sidebar-button ${isActive(item.path) ? 'active' : ''}`}
              title={label}
              aria-label={label}
            >
              {item.icon}
              {isExpanded && <span className="sidebar-label">{label}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
