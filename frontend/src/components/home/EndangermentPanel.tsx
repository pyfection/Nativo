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
  /** i18n key for the per-language body sentence. */
  bodyKey: string;
}

// UNESCO Atlas of the World's Languages in Danger, plus a couple of
// well-documented secondary sources. Update as the Atlas does — these are
// snapshots, not authoritative live data. The body sentences live in i18n
// (endangerment.body_{iso}) so they're translatable per UI language.
const DATA: Record<string, LanguageEndangermentData> = {
  bar: { level: 'vulnerable', levelLabel: 'Vulnerable', bodyKey: 'endangerment.body_bar' },
  umu: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    bodyKey: 'endangerment.body_umu',
  },
  haw: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    bodyKey: 'endangerment.body_haw',
  },
  nav: { level: 'vulnerable', levelLabel: 'Vulnerable', bodyKey: 'endangerment.body_nav' },
  ain: {
    level: 'critically-endangered',
    levelLabel: 'Critically endangered',
    bodyKey: 'endangerment.body_ain',
  },
  eng: { level: 'safe', levelLabel: 'Safe', bodyKey: 'endangerment.body_eng' },
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
        <p className="endangerment-body">{t(data.bodyKey)}</p>

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
