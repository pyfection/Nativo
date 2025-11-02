import { useAuth } from '../../contexts/AuthContext';
import Sidebar from '../common/Sidebar';
import LanguageSelector from '../common/LanguageSelector';
import UserMenu from '../common/UserMenu';
import { Language } from '../../App';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  languages: Language[];
}

export default function AppLayout({ children, selectedLanguage, onLanguageChange, languages }: AppLayoutProps) {
  const { isAuthenticated, refreshUserProficiencies } = useAuth();

  const handleLanguageJoined = async () => {
    await refreshUserProficiencies();
  };

  return (
    <div className="app-layout">
      {/* Top Header */}
      <header className="app-header">
        <div className="app-header-content">
          <h1 className="app-logo">Nativo</h1>
          <div className="app-header-right">
            <LanguageSelector
              languages={languages}
              selectedLanguage={selectedLanguage}
              onLanguageChange={onLanguageChange}
              onLanguageJoined={handleLanguageJoined}
            />
            <UserMenu />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="app-content-wrapper">
        {isAuthenticated && <Sidebar />}
        <main className={`app-main ${isAuthenticated ? 'with-sidebar' : ''}`}>
          {children}
        </main>
      </div>
    </div>
  );
}

