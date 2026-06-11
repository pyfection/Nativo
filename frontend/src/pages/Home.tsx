import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import HomeDictionary from '../components/home/HomeDictionary';
import LanguageActionPanel from '../components/home/LanguageActionPanel';
import RecentActivity from '../components/home/RecentActivity';
import { getStatistics, Statistics } from '../services/statisticsService';
import './Home.css';

interface HomeProps {
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
  languages: Language[];
}

const EMPTY_STATS: Statistics = {
  total_languages: 0,
  total_words: 0,
  total_audio: 0,
  total_documents: 0,
  total_contributors: 0,
};

export default function Home({ selectedLanguage }: HomeProps) {
  const { t } = useTranslation();
  const [languageStats, setLanguageStats] = useState<Statistics>(EMPTY_STATS);
  const [platformStats, setPlatformStats] = useState<Statistics>(EMPTY_STATS);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setStatsLoading(true);
    Promise.all([getStatistics(selectedLanguage.id), getStatistics()])
      .then(([lang, platform]) => {
        if (cancelled) return;
        setLanguageStats(lang);
        setPlatformStats(platform);
      })
      .catch((error) => {
        // Network/CORS — leave defaults, log
        console.error('Failed to fetch statistics:', error);
      })
      .finally(() => {
        if (!cancelled) setStatsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  const renderStats = (stats: Statistics, includeLanguageCount: boolean) => {
    const cells: Array<{ value: number; label: string }> = [];
    if (includeLanguageCount) {
      cells.push({ value: stats.total_languages, label: t('stats.languages') });
    }
    cells.push(
      { value: stats.total_words, label: t('stats.words') },
      { value: stats.total_documents, label: t('stats.documents') },
      { value: stats.total_audio, label: t('stats.audio') },
      { value: stats.total_contributors, label: t('stats.contributors') }
    );

    return (
      <div className="stats-grid">
        {cells.map((cell) => (
          <div key={cell.label} className="stat-card">
            <div className="stat-number">{statsLoading ? '…' : cell.value}</div>
            <div className="stat-label">{cell.label}</div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div
      className="home-page"
      style={
        {
          '--primary': selectedLanguage.colorScheme.primary,
          '--secondary': selectedLanguage.colorScheme.secondary,
          '--accent': selectedLanguage.colorScheme.accent,
          '--background': selectedLanguage.colorScheme.background,
        } as React.CSSProperties
      }
    >
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h2 className="hero-title">
            {t('hero.title_language', { language: selectedLanguage.name })}
          </h2>
          <p className="hero-subtitle">
            {t('hero.subtitle_language', { language: selectedLanguage.name })}
          </p>
          <div className="hero-language-info">
            <h3 className="language-name">{selectedLanguage.name}</h3>
            <p className="language-native">{selectedLanguage.nativeName}</p>
            <p className="language-description">{selectedLanguage.description}</p>
            <LanguageActionPanel />
          </div>
        </div>
      </section>

      {/* Dictionary widget */}
      <HomeDictionary selectedLanguage={selectedLanguage} />

      {/* Language-scoped stats */}
      <section className="stats-section">
        <h3 className="stats-heading">
          {t('stats.language_heading', { language: selectedLanguage.name })}
        </h3>
        {renderStats(languageStats, false)}
      </section>

      {/* Recent activity */}
      <RecentActivity selectedLanguage={selectedLanguage} />

      {/* Platform overview */}
      <section className="stats-section stats-section-platform">
        <h3 className="stats-heading">{t('stats.heading')}</h3>
        {renderStats(platformStats, true)}
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
