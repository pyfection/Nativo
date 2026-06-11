import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Language } from '../../App';
import wordService, { WordListItem } from '../../services/wordService';
import HomeDictionary from './HomeDictionary';
import './WordSpotlight.css';

interface WordSpotlightProps {
  selectedLanguage: Language;
}

const ROTATE_MS = 3000;
const FADE_MS = 300;

// Fisher–Yates so each visit shuffles the rotation order.
function shuffle<T>(arr: T[]): T[] {
  const out = arr.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export default function WordSpotlight({ selectedLanguage }: WordSpotlightProps) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<'rotating' | 'translate'>('rotating');
  const [words, setWords] = useState<WordListItem[]>([]);
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  // Fetch once per language; shuffle for variety per visit.
  useEffect(() => {
    let cancelled = false;
    wordService
      .getAll({ language_id: selectedLanguage.id, limit: 100 })
      .then((data) => {
        if (cancelled) return;
        setWords(shuffle(data));
        setIndex(0);
      })
      .catch(() => {
        if (cancelled) return;
        setWords([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  // Auto-rotate while in rotating mode and there are >= 2 words.
  useEffect(() => {
    if (mode !== 'rotating' || words.length < 2) return;
    const fadeOut = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex((i) => (i + 1) % words.length);
        setVisible(true);
      }, FADE_MS);
    }, ROTATE_MS);
    return () => clearInterval(fadeOut);
  }, [mode, words.length]);

  const current = useMemo(() => words[index], [words, index]);

  if (mode === 'translate') {
    return (
      <section className="word-spotlight">
        <div className="word-spotlight-inner">
          <HomeDictionary selectedLanguage={selectedLanguage} />
          <button
            type="button"
            className="word-spotlight-back"
            onClick={() => setMode('rotating')}
          >
            ← {t('spotlight.back')}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="word-spotlight">
      <div className="word-spotlight-inner">
        <p className="word-spotlight-eyebrow">
          {t('spotlight.eyebrow', { language: selectedLanguage.name })}
        </p>

        {words.length === 0 ? (
          <div className="word-spotlight-empty">{t('spotlight.empty')}</div>
        ) : (
          <div className={`word-spotlight-card ${visible ? 'visible' : 'fading'}`}>
            <div className="word-spotlight-word">{current?.word}</div>
            <div className="word-spotlight-meta">
              {current?.romanization && (
                <span className="word-spotlight-roman">/{current.romanization}/</span>
              )}
              {current?.part_of_speech && (
                <span className="word-spotlight-pos">{current.part_of_speech}</span>
              )}
            </div>
            {current?.definition && (
              <div className="word-spotlight-definition">{current.definition}</div>
            )}
          </div>
        )}

        <button
          type="button"
          className="word-spotlight-translate"
          onClick={() => setMode('translate')}
        >
          {t('spotlight.translate_cta')}
        </button>
      </div>
    </section>
  );
}
