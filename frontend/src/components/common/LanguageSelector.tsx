import { Language } from '../../App';
import './LanguageSelector.css';

interface LanguageSelectorProps {
  languages: Language[];
  selectedLanguage: Language;
  onLanguageChange: (language: Language) => void;
}

export default function LanguageSelector({ 
  languages, 
  selectedLanguage, 
  onLanguageChange 
}: LanguageSelectorProps) {
  return (
    <div className="language-selector">
      <label htmlFor="language-select" className="selector-label">
        Language:
      </label>
      <select
        id="language-select"
        value={selectedLanguage.id}
        onChange={(e) => {
          const language = languages.find(lang => lang.id === e.target.value);
          if (language) {
            onLanguageChange(language);
          }
        }}
        className="selector-dropdown"
      >
        {languages.map((language) => (
          <option key={language.id} value={language.id}>
            {language.name} ({language.nativeName})
          </option>
        ))}
      </select>
    </div>
  );
}

