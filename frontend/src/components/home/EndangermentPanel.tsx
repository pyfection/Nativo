import { useTranslation } from 'react-i18next';

import { Language } from '../../App';
import './EndangermentPanel.css';

interface EndangermentPanelProps {
  selectedLanguage: Language;
  wordCount: number;
  loading?: boolean;
}

type Level =
  | 'safe'
  | 'vulnerable'
  | 'definitely-endangered'
  | 'severely-endangered'
  | 'critically-endangered'
  | 'extinct';

interface LanguageEndangermentData {
  level: Level;
  /** Human-readable level for the badge. */
  levelLabel: string;
  /** A short explanation specific to this language. English baked-in for now;
   *  for Bavarian/other UI languages this stays as English fallback until
   *  per-language translations are reviewed. */
  body: string;
}

// UNESCO Atlas of the World's Languages in Danger, plus a couple of
// well-documented secondary sources. Update as the Atlas does — these are
// snapshots, not authoritative live data.
const DATA: Record<string, LanguageEndangermentData> = {
  bar: {
    level: 'vulnerable',
    levelLabel: 'Vulnerable',
    body: 'Most children still speak it, but increasingly only in informal settings.',
  },
  umu: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    body: 'The youngest fluent speakers are in their seventies and older.',
  },
  haw: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    body: 'A revitalization movement is underway; fluent native speakers remain few.',
  },
  nav: {
    level: 'vulnerable',
    levelLabel: 'Vulnerable',
    body: 'Still the most widely spoken Indigenous language in North America, but younger speakers are declining.',
  },
  ain: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    body: 'Only a handful of fully fluent speakers remain, most very elderly.',
  },
  eng: {
    level: 'safe',
    levelLabel: 'Safe',
    body: 'Spoken by all generations across many regions; not classified as endangered.',
  },
};

const CORE_WORDS_TARGET = 5000;

export default function EndangermentPanel({
  selectedLanguage,
  wordCount,
  loading,
}: EndangermentPanelProps) {
  const { t } = useTranslation();
  const data = DATA[selectedLanguage.iso] ?? DATA.bar;
  const percent = Math.min(100, (wordCount / CORE_WORDS_TARGET) * 100);

  return (
    <section className={`endangerment endangerment-${data.level}`}>
      <div className="endangerment-inner">
        <div className="endangerment-badge">{data.levelLabel}</div>
        <h3 className="endangerment-title">
          {t('endangerment.headline', {
            language: selectedLanguage.name,
            level: data.levelLabel.toLowerCase(),
          })}
        </h3>
        <p className="endangerment-body">{data.body}</p>

        {data.level !== 'safe' && (
          <div className="endangerment-progress">
            <div className="endangerment-progress-bar" aria-hidden="true">
              <div
                className="endangerment-progress-fill"
                style={{ width: `${Math.max(percent, 0.5)}%` }}
              />
            </div>
            <div className="endangerment-progress-label">
              {t('endangerment.progress', {
                count: loading ? '…' : wordCount,
                target: CORE_WORDS_TARGET.toLocaleString(),
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
