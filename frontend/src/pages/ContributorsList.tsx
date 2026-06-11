import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import { ContributorItem, listContributors } from '../services/contributorsService';
import './ContributorsList.css';

interface ContributorsListProps {
  selectedLanguage: Language;
}

export default function ContributorsList({ selectedLanguage }: ContributorsListProps) {
  const { t } = useTranslation();
  const [items, setItems] = useState<ContributorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listContributors(selectedLanguage.id)
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load contributors');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  return (
    <div className="contributors-page">
      <header className="contributors-header">
        <h1>{t('contributors_page.title', { language: selectedLanguage.name })}</h1>
        <p className="contributors-subtitle">{t('contributors_page.subtitle')}</p>
      </header>

      {loading && <p className="contributors-status">{t('contributors_page.loading')}</p>}
      {error && <p className="contributors-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <div className="contributors-empty">
          <p>{t('contributors_page.empty')}</p>
        </div>
      )}

      {items.length > 0 && (
        <table className="contributors-table">
          <thead>
            <tr>
              <th>{t('contributors_page.col_user')}</th>
              <th>{t('contributors_page.col_proficiency')}</th>
              <th className="num">{t('contributors_page.col_words')}</th>
              <th className="num">{t('contributors_page.col_documents')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>
                  <div className="contributors-user">
                    <div className="contributors-avatar">
                      {c.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="contributors-username">{c.username}</div>
                      <div className="contributors-role">{c.role}</div>
                    </div>
                  </div>
                </td>
                <td>
                  {c.proficiency_level ? (
                    <span className="contributors-proficiency">{c.proficiency_level}</span>
                  ) : (
                    <span className="contributors-no-proficiency">—</span>
                  )}
                </td>
                <td className="num">{c.word_count}</td>
                <td className="num">{c.text_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
