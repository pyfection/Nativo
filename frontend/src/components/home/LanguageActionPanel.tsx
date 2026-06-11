import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import './LanguageActionPanel.css';

export default function LanguageActionPanel() {
  const { t } = useTranslation();

  return (
    <div className="language-action-panel">
      <Link className="language-action" to="/words">
        <span className="language-action-icon" aria-hidden="true">📝</span>
        {t('action_panel.view_words')}
      </Link>
      <Link className="language-action" to="/documents">
        <span className="language-action-icon" aria-hidden="true">📚</span>
        {t('action_panel.view_documents')}
      </Link>
      <span
        className="language-action language-action-disabled"
        title={t('action_panel.upload_audio_coming_soon')}
      >
        <span className="language-action-icon" aria-hidden="true">🎙️</span>
        {t('action_panel.upload_audio')}
      </span>
      <Link className="language-action language-action-primary" to="/languages">
        <span className="language-action-icon" aria-hidden="true">🤝</span>
        {t('action_panel.contribute')}
      </Link>
    </div>
  );
}
