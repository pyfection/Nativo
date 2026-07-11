import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../App';
import EndangermentPanel from '../components/home/EndangermentPanel';
import HomeHeroCard from '../components/home/HomeHeroCard';
import LanguageActionPanel from '../components/home/LanguageActionPanel';
import LatestText from '../components/home/LatestText';
import RecentActivity from '../components/home/RecentActivity';
import StatCard from '../components/home/StatCard';
import { useAuth } from '../contexts/AuthContext';
import { getStatistics, Statistics } from '../services/statisticsService';
import './Home.css';
import { languageDisplayName, languageDisplayDescription } from '../utils/languageName';

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
          isAuthenticated ? (
            <Link className="stat-cta-link" to="/words">
              {t('stats.cta_add_audio')}
            </Link>
          ) : (
            <Link className="stat-cta-link" to="/register">
              {t('stats.cta_join_to_contribute')}
            </Link>
          )
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
    <div className="home-page">
      {/* ---------- Hero ---------- */}
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="dot"></span>
            {t('hero_v2.eyebrow')}
          </div>
          <h1 className="hero-h1">
            {t('hero_v2.heading_pre')}{' '}
            <em>{t('hero_v2.heading_emphasis')}</em>
            <br />
            {t('hero_v2.heading_post')}
          </h1>
          <p className="hero-sub">
            {t('hero_v2.sub', { language: languageDisplayName(selectedLanguage) })}
          </p>
          <div className="hero-actions">
            {isAuthenticated ? (
              <>
                <Link to="/words/add" className="btn btn-accent btn-lg">
                  {t('hero_v2.cta_start')}
                </Link>
                <Link to="/languages" className="btn btn-ghost btn-lg">
                  {t('hero_v2.cta_explore')}
                </Link>
              </>
            ) : (
              // Curiosity first, commitment later: guests get "browse the
              // dictionary" as the primary action, signup as the secondary.
              <>
                <Link to="/dictionary" className="btn btn-accent btn-lg">
                  {t('hero_v2.cta_browse')}
                </Link>
                <Link to="/register" className="btn btn-ghost btn-lg">
                  {t('hero_v2.cta_start')}
                </Link>
              </>
            )}
          </div>
          <div className="hero-reassure">
            <i>✦</i> {t('hero_v2.reassure')}
          </div>
        </div>

        <HomeHeroCard selectedLanguage={selectedLanguage} />
      </section>

      {/* ---------- The selected language ---------- */}
      <section className="language-strip">
        <div className="language-strip-inner">
          <h3 className="language-strip-name">{languageDisplayName(selectedLanguage)}</h3>
          <p className="language-strip-native">{selectedLanguage.nativeName}</p>
          {languageDisplayDescription(selectedLanguage) && (
            <p className="language-strip-desc">{languageDisplayDescription(selectedLanguage)}</p>
          )}
          <LanguageActionPanel />
          {/* Most contributors will want to read the orthography rules before
              they write a word; surface that link right next to the language
              header so it's the most-visible reference on the page. */}
          {selectedLanguage.writingStandardDocumentId && (
            <Link
              to={`/languages/${selectedLanguage.id}/standard`}
              className="language-strip-standard"
              title={`Read the orthography / writing rules for ${selectedLanguage.name}`}
            >
              📖 {t('home.read_writing_standard', { language: languageDisplayName(selectedLanguage) })}
            </Link>
          )}
        </div>
      </section>

      {/* Something real to read, one click from landing */}
      <LatestText selectedLanguage={selectedLanguage} />

      {/* UNESCO endangerment + progress towards a core-vocabulary target */}
      <EndangermentPanel
        selectedLanguage={selectedLanguage}
        wordCount={languageStats.total_words}
        loading={statsLoading}
      />

      {/* Language-scoped stats */}
      <section className="stats-section">
        <h3 className="stats-heading">
          {t('stats.language_heading', { language: languageDisplayName(selectedLanguage) })}
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

      <footer className="footer">
        <p>{t('footer.copyright')}</p>
      </footer>
    </div>
  );
}
