import { useUILanguage } from '../../contexts/UILanguageContext';
import './UILanguageSelector.css';

export default function UILanguageSelector() {
  const { uiLanguage, setUILanguageId, candidates } = useUILanguage();

  if (candidates.length === 0) return null;

  return (
    <label className="ui-language-selector" title="Interface language">
      <span className="ui-language-icon" aria-hidden="true">🌐</span>
      <select
        className="ui-language-select"
        value={uiLanguage?.id ?? ''}
        onChange={(e) => setUILanguageId(e.target.value)}
        aria-label="Interface language"
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
