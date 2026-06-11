import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Link } from 'react-router-dom';

import { Language } from '../App';
import EndangermentPanel from '../components/home/EndangermentPanel';
import LanguageActionPanel from '../components/home/LanguageActionPanel';
import RecentActivity from '../components/home/RecentActivity';
import StatCard from '../components/home/StatCard';
import WordSpotlight from '../components/home/WordSpotlight';
import { useAuth } from '../contexts/AuthContext';
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
  const { isAuthenticated } = useAuth();
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

  const renderLanguageStats = (stats: Statistics) => (
    <div className="stats-grid">
      <StatCard
        value={stats.total_words}
        label={t('stats.words')}
        href="/words"
        loading={statsLoading}
        zeroCta={
          isAuthenticated ? (
            <Link className="stat-cta-link" to="/words/add">
              {t('stats.cta_add_word')}
            </Link>
          ) : (
            <Link className="stat-cta-link" to="/register">
              {t('stats.cta_join_to_contribute')}
            </Link>
          )
        }
      />
      <StatCard
        value={stats.total_documents}
        label={t('stats.documents')}
        href="/documents"
        loading={statsLoading}
        zeroCta={
          isAuthenticated ? (
            <Link className="stat-cta-link" to="/documents/add">
              {t('stats.cta_add_document')}
            </Link>
          ) : (
            <Link className="stat-cta-link" to="/register">
              {t('stats.cta_join_to_contribute')}
            </Link>
          )
        }
      />
      <StatCard
        value={stats.total_audio}
        label={t('stats.audio')}
        href="/audio"
        loading={statsLoading}
        zeroCta={
          <span className="stat-cta-coming-soon" title={t('action_panel.upload_audio_coming_soon')}>
            {t('stats.cta_audio_coming_soon')}
          </span>
        }
      />
      <StatCard
        value={stats.total_contributors}
        label={t('stats.contributors')}
        href="/contributors"
        loading={statsLoading}
      />
    </div>
  );

  const renderPlatformStats = (stats: Statistics) => (
    <div className="stats-grid">
      <StatCard value={stats.total_languages} label={t('stats.languages')} href="/languages" loading={statsLoading} />
      <StatCard value={stats.total_words} label={t('stats.words')} href="/words" loading={statsLoading} />
      <StatCard value={stats.total_documents} label={t('stats.documents')} href="/documents" loading={statsLoading} />
      <StatCard value={stats.total_audio} label={t('stats.audio')} href="/audio" loading={statsLoading} />
      <StatCard
        value={stats.total_contributors}
        label={t('stats.contributors')}
        href="/contributors"
        loading={statsLoading}
      />
    </div>
  );

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

      {/* UNESCO endangerment + progress towards a core-vocabulary target */}
      <EndangermentPanel
        selectedLanguage={selectedLanguage}
        wordCount={languageStats.total_words}
        loading={statsLoading}
      />

      {/* Random word spotlight (rotates every 3s; reveals the dictionary on Translate) */}
      <WordSpotlight selectedLanguage={selectedLanguage} />

      {/* Language-scoped stats */}
      <section className="stats-section">
        <h3 className="stats-heading">
          {t('stats.language_heading', { language: selectedLanguage.name })}
        </h3>
        {renderLanguageStats(languageStats)}
      </section>

      {/* Recent activity */}
      <RecentActivity selectedLanguage={selectedLanguage} />

      {/* Platform overview */}
      <section className="stats-section stats-section-platform">
        <h3 className="stats-heading">{t('stats.heading')}</h3>
        {renderPlatformStats(platformStats)}
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
