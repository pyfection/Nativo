import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import './Sidebar.css';

interface NavItem {
  path: string;
  labelKey: string;
  icon: JSX.Element;
}

// All icons use stroke="currentColor" + fill="none" line-art style for a
// consistent look that inherits the link colour (sage on idle, cream on
// hover, accent on active). Mixing filled silhouettes with hardcoded
// fill="white" inner shapes — the previous documents icon — renders as a
// black slab on dark backgrounds.
const ICON_PROPS = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
};

const NAV_ITEMS: NavItem[] = [
  {
    path: '/words',
    labelKey: 'nav.words',
    // Custom "Αω" glyph icon — fill is fine here because <text> doesn't
    // default to a hardcoded colour the way <path> does.
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
        <text
          x="12"
          y="17"
          textAnchor="middle"
          fontSize="16"
          fontFamily="'Times New Roman', Georgia, serif"
          fontWeight="600"
          fill="currentColor"
        >
          Αω
        </text>
      </svg>
    ),
  },
  {
    path: '/dictionary',
    labelKey: 'nav.dictionary',
    // Open book
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M2 4.5C5 3.5 8.5 3.5 12 5.5C15.5 3.5 19 3.5 22 4.5V19C19 18 15.5 18 12 20C8.5 18 5 18 2 19V4.5Z" />
        <path d="M12 5.5V20" />
      </svg>
    ),
  },
  {
    path: '/spelling',
    labelKey: 'nav.spelling',
    // Pencil writing on a line — "how is this spelled?"
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M4 20H20" />
        <path d="M14.5 4.5L18 8L8 18H4.5V14.5L14.5 4.5Z" />
      </svg>
    ),
  },
  {
    path: '/documents',
    labelKey: 'nav.documents',
    // Sheet of paper with text lines
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M6 2H15L19 6V20C19 21.1 18.1 22 17 22H6C4.9 22 4 21.1 4 20V4C4 2.9 4.9 2 6 2Z" />
        <path d="M14 2V7H19" />
        <path d="M8 11H15" />
        <path d="M8 15H15" />
        <path d="M8 19H12" />
      </svg>
    ),
  },
  {
    path: '/audio',
    labelKey: 'nav.audio',
    // Equaliser-style waveform
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M4 10V14" />
        <path d="M8 7V17" />
        <path d="M12 4V20" />
        <path d="M16 7V17" />
        <path d="M20 10V14" />
      </svg>
    ),
  },
  {
    path: '/contributors',
    labelKey: 'nav.contributors',
    // Two-person group
    icon: (
      <svg {...ICON_PROPS}>
        <path d="M16 21V19C16 17.9 15.1 17 14 17H6C4.9 17 4 17.9 4 19V21" />
        <circle cx="10" cy="9" r="3.5" />
        <path d="M20 21V19C20 17.5 19 16.2 17.5 15.9" />
        <path d="M15.5 5.5C16.7 6 17.5 7.2 17.5 8.5C17.5 9.8 16.7 11 15.5 11.5" />
      </svg>
    ),
  },
  {
    path: '/languages',
    labelKey: 'nav.languages',
    // Globe with latitude + longitude lines
    icon: (
      <svg {...ICON_PROPS}>
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12H21" />
        <path d="M12 3C14.5 5.7 15.9 8.8 15.9 12C15.9 15.2 14.5 18.3 12 21C9.5 18.3 8.1 15.2 8.1 12C8.1 8.8 9.5 5.7 12 3Z" />
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
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
          title={isExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
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
