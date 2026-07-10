import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../../App';
import documentService from '../../services/documentService';
import { DocumentListItem } from '../../types/document';
import './LatestText.css';

interface LatestTextProps {
  selectedLanguage: Language;
}

/**
 * Teaser for the newest text in the selected language: title + excerpt,
 * linking to the full document. Gives a visitor something real to read
 * within one click of landing. Renders nothing while loading or when the
 * language has no texts yet — the stats grid already covers the empty case.
 */
export default function LatestText({ selectedLanguage }: LatestTextProps) {
  const { t } = useTranslation();
  const [doc, setDoc] = useState<DocumentListItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDoc(null);
    documentService
      .getAll({ language_id: selectedLanguage.id })
      .then((docs) => {
        if (cancelled || docs.length === 0) return;
        const newest = docs
          .slice()
          .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))[0];
        setDoc(newest);
      })
      .catch(() => {
        // Teaser is best-effort decoration; a fetch error just hides it.
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  if (!doc) return null;

  return (
    <section className="latest-text">
      <h3 className="latest-text-heading">
        {t('latest_text.heading', { language: selectedLanguage.name })}
      </h3>
      <Link to={`/documents/${doc.id}`} className="latest-text-card card">
        <h4 className="latest-text-title">{doc.title}</h4>
        {doc.content_preview && <p className="latest-text-excerpt">{doc.content_preview}</p>}
        <span className="latest-text-more">{t('latest_text.read_more')} →</span>
      </Link>
    </section>
  );
}
