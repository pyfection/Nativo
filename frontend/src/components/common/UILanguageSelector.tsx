import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { useUILanguage } from '../../contexts/UILanguageContext';
import Dropdown, { DropdownOption } from './Dropdown';
import './UILanguageSelector.css';

export default function UILanguageSelector() {
  const { t } = useTranslation();
  const { uiLanguage, setUILanguageId, candidates } = useUILanguage();

  const options = useMemo<DropdownOption<string>[]>(
    () =>
      candidates.map((l) => ({
        value: l.id,
        label: l.name,
      })),
    [candidates],
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
