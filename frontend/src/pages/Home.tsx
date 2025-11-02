import { useEffect, useState } from 'react';
import { Language } from '../App';
import { getStatistics, Statistics } from '../services/statisticsService';
import './Home.css';

interface HomeProps {
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  languages: Language[];
}

export default function Home({ selectedLanguage, onLanguageChange, languages }: HomeProps) {
  const [stats, setStats] = useState<Statistics>({
    total_languages: 0,
    total_words: 0,
    total_audio: 0,
    total_documents: 0,
    total_contributors: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getStatistics();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="home-page" style={{
      '--primary': selectedLanguage.colorScheme.primary,
      '--secondary': selectedLanguage.colorScheme.secondary,
      '--accent': selectedLanguage.colorScheme.accent,
      '--background': selectedLanguage.colorScheme.background,
    } as React.CSSProperties}>
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
            <div className="stat-number">
              {isLoading ? '...' : stats.total_languages}
            </div>
            <div className="stat-label">Languages Preserved</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_words}
            </div>
            <div className="stat-label">Words Documented</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_documents}
            </div>
            <div className="stat-label">Documents Preserved</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_audio}
            </div>
            <div className="stat-label">Audio Recordings</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_contributors}
            </div>
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

