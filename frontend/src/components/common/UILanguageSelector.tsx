import { useTranslation } from 'react-i18next';

import { useUILanguage } from '../../contexts/UILanguageContext';
import './UILanguageSelector.css';

export default function UILanguageSelector() {
  const { t } = useTranslation();
  const { uiLanguage, setUILanguageId, candidates } = useUILanguage();

  if (candidates.length === 0) return null;
  const label = t('header.interface_language');

  return (
    <label className="ui-language-selector" title={label}>
      <span className="ui-language-icon" aria-hidden="true">🌐</span>
      <select
        className="ui-language-select"
        value={uiLanguage?.id ?? ''}
        onChange={(e) => setUILanguageId(e.target.value)}
        aria-label={label}
      >
        {candidates.map((l) => (
          <option key={l.id} value={l.id}>
            {l.name}
          </option>
        ))}
      </select>
    </label>
  );
}
