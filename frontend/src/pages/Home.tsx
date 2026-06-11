import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import HomeDictionary from '../components/home/HomeDictionary';
import { getStatistics, Statistics } from '../services/statisticsService';
import './Home.css';

interface HomeProps {
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  languages: Language[];
}

export default function Home({ selectedLanguage }: HomeProps) {
  const { t } = useTranslation();
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
          <h2 className="hero-title">{t('hero.title')}</h2>
          <p className="hero-subtitle">{t('hero.subtitle')}</p>
          <div className="hero-language-info">
            <h3 className="language-name">{selectedLanguage.name}</h3>
            <p className="language-native">{selectedLanguage.nativeName}</p>
            <p className="language-description">{selectedLanguage.description}</p>
          </div>
        </div>
      </section>

      {/* Dictionary widget */}
      <HomeDictionary selectedLanguage={selectedLanguage} />

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_languages}
            </div>
            <div className="stat-label">{t('stats.languages')}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_words}
            </div>
            <div className="stat-label">{t('stats.words')}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_documents}
            </div>
            <div className="stat-label">{t('stats.documents')}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_audio}
            </div>
            <div className="stat-label">{t('stats.audio')}</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">
              {isLoading ? '...' : stats.total_contributors}
            </div>
            <div className="stat-label">{t('stats.contributors')}</div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="mission-section">
        <div className="mission-content">
          <h3 className="mission-title">{t('mission.title')}</h3>
          <div className="mission-grid">
            <div className="mission-card">
              <div className="mission-icon">📚</div>
              <h4>{t('mission.document_title')}</h4>
              <p>{t('mission.document_body')}</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">💬</div>
              <h4>{t('mission.vocabulary_title')}</h4>
              <p>{t('mission.vocabulary_body')}</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">🎙️</div>
              <h4>{t('mission.audio_title')}</h4>
              <p>{t('mission.audio_body')}</p>
            </div>
            <div className="mission-card">
              <div className="mission-icon">🌍</div>
              <h4>{t('mission.share_title')}</h4>
              <p>{t('mission.share_body')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>{t('footer.copyright')}</p>
      </footer>
    </div>
  );
}
