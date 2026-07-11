import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { useUILanguage } from '../../contexts/UILanguageContext';
import { languageDisplayName } from '../../utils/languageName';
import Dropdown, { DropdownOption } from './Dropdown';
import './UILanguageSelector.css';

export default function UILanguageSelector() {
  const { t, i18n } = useTranslation();
  const { uiLanguage, setUILanguageId, candidates } = useUILanguage();

  const options = useMemo<DropdownOption<string>[]>(
    () =>
      candidates.map((l) => ({
        value: l.id,
        label: languageDisplayName(l),
      })),
    // i18n.language: labels are localized, recompute on UI-language change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [candidates, i18n.language],
  );

  if (candidates.length === 0) return null;
  const label = t('header.interface_language');

  return (
    <Dropdown
      className="ui-language-selector"
      value={uiLanguage?.id ?? ''}
      options={options}
      onChange={(id) => setUILanguageId(id)}
      ariaLabel={label}
      align="right"
      triggerPrefix={
        <span className="ui-language-icon" aria-hidden="true">
          🌐
        </span>
      }
    />
  );
}
