import { Language } from '../App';
import LanguageSelector from '../components/common/LanguageSelector';
import UserMenu from '../components/common/UserMenu';
import './Home.css';

interface HomeProps {
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  languages: Language[];
}

export default function Home({ selectedLanguage, onLanguageChange, languages }: HomeProps) {
  // Hardcoded stats for now
  const stats = {
    totalLanguages: 5,
    wordsDocumented: 1247,
    audioRecordings: 389,
    contributors: 42,
  };

  return (
    <div className="home-page" style={{
      '--primary': selectedLanguage.colorScheme.primary,
      '--secondary': selectedLanguage.colorScheme.secondary,
      '--accent': selectedLanguage.colorScheme.accent,
      '--background': selectedLanguage.colorScheme.background,
    } as React.CSSProperties}>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="logo">Nativo</h1>
          <div className="header-right">
            <LanguageSelector
              languages={languages}
              selectedLanguage={selectedLanguage}
              onLanguageChange={onLanguageChange}
            />
            <UserMenu />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h2 className="hero-title">
            Preserving Endangered Languages
          </h2>
          <p className="hero-subtitle">
            A digital platform dedicated to documenting and preserving the world's endangered languages
            through written documents, vocabulary databases, and audio recordings.
          </p>
          <div className="hero-language-info">
            <h3 className="language-name">{selectedLanguage.name}</h3>
            <p className="language-native">{selectedLanguage.nativeName}</p>
            <p className="language-description">{selectedLanguage.description}</p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">{stats.totalLanguages}</div>
            <div className="stat-label">Languages Preserved</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.wordsDocumented}</div>
            <div className="stat-label">Words Documented</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.audioRecordings}</div>
            <div className="stat-label">Audio Recordings</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.contributors}</div>
            <div className="stat-label">Contributors</div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="mission-section">
        <div className="mission-content">
          <h3 className="mission-title">Our Mission</h3>
          <div className="mission-grid">
            <div className="mission-card">
              <div className="mission-icon">📚</div>
              <h4>Document</h4>
              <p>Record and preserve written documents in endangered languages</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">💬</div>
              <h4>Build Vocabulary</h4>
              <p>Create comprehensive databases with translations and pronunciations</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">🎙️</div>
              <h4>Record Audio</h4>
              <p>Store authentic recordings of native speakers</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">🌍</div>
              <h4>Share Knowledge</h4>
              <p>Make linguistic heritage accessible for future generations</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 Nativo - Preserving Linguistic Heritage</p>
      </footer>
    </div>
  );
}

