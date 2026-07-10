import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { Language } from '../../App';
import { useUILanguage } from '../../contexts/UILanguageContext';
import { fullAudioUrl, listAudioForForm } from '../../services/audioService';
import wordService, {
  LexemeWithForms,
  TranslationLink,
  WordListItem,
} from '../../services/wordService';
import './HomeHeroCard.css';

interface HomeHeroCardProps {
  selectedLanguage: Language;
}

const ROTATE_MS = 3500;
const FADE_MS = 300;

function shuffle<T>(arr: T[]): T[] {
  const out = arr.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

interface SearchHit extends LexemeWithForms {
  translations?: TranslationLink[];
}

/**
 * Unified hero card: shows rotating dictionary entries when idle and pivots
 * into a search result (or "no entry yet" empty state) on input. Replaces
 * the previous WordSpotlight + HomeDictionary pair.
 */
export default function HomeHeroCard({ selectedLanguage }: HomeHeroCardProps) {
  const { t } = useTranslation();
  const { uiLanguage } = useUILanguage();
  const target = uiLanguage && uiLanguage.id !== selectedLanguage.id ? uiLanguage : null;

  const [words, setWords] = useState<WordListItem[]>([]);
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(true);

  const [query, setQuery] = useState('');
  const [hit, setHit] = useState<SearchHit | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  // Fetch + shuffle the rotation pool whenever the language changes.
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
    // Reset search state on language change.
    setQuery('');
    setHit(null);
    setSearchError(null);
    setSearched(false);
    return () => {
      cancelled = true;
    };
  }, [selectedLanguage.id]);

  const inSearchMode = query.trim().length > 0 || searched;

  const current = useMemo(() => words[index], [words, index]);

  // Inline pronunciation for the entry on display — hearing the language is
  // the strongest hook the card has, especially for logged-out visitors.
  // Cache lexeme -> audio URL (or null) so rotation doesn't refetch.
  const audioCacheRef = useRef(new Map<string, string | null>());
  const playerRef = useRef<HTMLAudioElement | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  const activeEntry = inSearchMode ? hit : current;

  useEffect(() => {
    let cancelled = false;
    playerRef.current?.pause();
    setPlaying(false);
    setAudioUrl(null);
    if (!activeEntry) return;
    const lexemeId = activeEntry.id;
    const cached = audioCacheRef.current.get(lexemeId);
    if (cached !== undefined) {
      setAudioUrl(cached);
      return;
    }
    (async () => {
      let url: string | null = null;
      try {
        let forms =
          'forms' in activeEntry ? (activeEntry as LexemeWithForms).forms : undefined;
        if (!forms) forms = (await wordService.getById(lexemeId)).forms;
        const lemmaForm = forms?.find((f) => f.is_lemma) ?? forms?.[0];
        if (lemmaForm) {
          const audios = await listAudioForForm(lemmaForm.id);
          if (audios.length > 0) url = fullAudioUrl(audios[0].file_path);
        }
      } catch {
        // No audio is a normal state; stay silent.
      }
      audioCacheRef.current.set(lexemeId, url);
      if (!cancelled) setAudioUrl(url);
    })();
    return () => {
      cancelled = true;
    };
  }, [activeEntry]);

  function togglePlay() {
    if (!audioUrl) return;
    if (playing) {
      playerRef.current?.pause();
      setPlaying(false);
      return;
    }
    if (!playerRef.current || playerRef.current.src !== audioUrl) {
      playerRef.current?.pause();
      playerRef.current = new Audio(audioUrl);
      playerRef.current.onended = () => setPlaying(false);
    }
    void playerRef.current.play();
    setPlaying(true);
  }

  // Rotate every ROTATE_MS while in idle/rotating mode; hold the current
  // entry while its pronunciation is playing.
  useEffect(() => {
    if (inSearchMode || playing || words.length < 2) return;
    const tick = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIndex((i) => (i + 1) % words.length);
        setVisible(true);
      }, FADE_MS);
    }, ROTATE_MS);
    return () => clearInterval(tick);
  }, [inSearchMode, playing, words.length]);

  async function runSearch() {
    const trimmed = query.trim();
    if (!trimmed) {
      // Empty input → back to rotation
      setHit(null);
      setSearched(false);
      setSearchError(null);
      return;
    }
    setSearching(true);
    setSearchError(null);
    setSearched(true);
    try {
      const data = await wordService.search({
        q: trimmed,
        language_ids: selectedLanguage.id,
        include_unpublished: true,
      });
      if (data.length === 0) {
        setHit(null);
        return;
      }
      const enriched = { ...data[0] } as SearchHit;
      try {
        enriched.translations = await wordService.listTranslations(data[0].id);
      } catch {
        enriched.translations = [];
      }
      setHit(enriched);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setSearchError(t('dictionary.rate_limited'));
      } else {
        setSearchError(err.response?.data?.detail || t('dictionary.search_failed'));
      }
      setHit(null);
    } finally {
      setSearching(false);
    }
  }

  function onQueryChange(value: string) {
    setQuery(value);
    if (value.trim() === '') {
      // pivot back to rotation immediately
      setHit(null);
      setSearched(false);
      setSearchError(null);
    }
  }

  const targetTranslations = target && hit?.translations
    ? hit.translations.filter((tr) => tr.language_id === target.id)
    : [];

  return (
    <div className="hero-card card">
      <h2 className="hero-card-title">
        {t('hero_card.title', { language: selectedLanguage.name })}
      </h2>
      <p className="hero-card-hint">{t('hero_card.hint')}</p>

      <div className="hero-card-search">
        <input
          type="text"
          className="hero-card-input"
          placeholder={t('hero_card.placeholder')}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') runSearch();
          }}
          aria-label={t('hero_card.search_aria')}
        />
        <button
          type="button"
          className="btn btn-accent hero-card-go"
          onClick={runSearch}
          disabled={searching || !query.trim()}
        >
          {searching ? t('dictionary.searching') : t('dictionary.search')}
        </button>
      </div>

      <div className="hero-card-panel">
        {searchError && <p className="hero-card-error">{searchError}</p>}

        {/* Search result */}
        {!searchError && inSearchMode && hit && (
          <div className="hero-card-entry visible">
            <div className="hero-card-label">
              <span>{t('hero_card.label_result')}</span>
              <span>{selectedLanguage.nativeName}</span>
            </div>
            <div className="hero-card-word">
              {hit.lemma}
              {audioUrl && (
                <button
                  type="button"
                  className="hero-card-play"
                  onClick={togglePlay}
                  title={t('hero_card.play')}
                >
                  {playing ? '❚❚' : '▶'} {t('hero_card.play')}
                </button>
              )}
            </div>
            <HeroCardMeta lexeme={hit} />
            {target && (
              <div className="hero-card-gloss">
                <span className="hero-card-gloss-key">{target.name}</span>
                <span className="hero-card-gloss-val">
                  {targetTranslations.length > 0
                    ? targetTranslations.map((tr) => tr.lemma).join(', ')
                    : t('hero_card.no_translation_in_target', { target: target.name })}
                </span>
              </div>
            )}
            <div className="hero-card-footer">
              <Link className="hero-card-link" to={`/words/${hit.id}`}>
                {t('hero_card.view_in_dictionary')} →
              </Link>
            </div>
          </div>
        )}

        {/* Empty search */}
        {!searchError && inSearchMode && !hit && !searching && (
          <div className="hero-card-empty">
            <div className="hero-card-empty-big">
              {t('hero_card.no_entry', { query: query.trim() })}
            </div>
            <p>{t('hero_card.no_entry_body', { language: selectedLanguage.name })}</p>
            <Link className="btn btn-accent" to="/register">
              {t('hero_card.add_this_word')}
            </Link>
          </div>
        )}

        {/* Rotating dictionary entries */}
        {!inSearchMode && words.length === 0 && (
          <div className="hero-card-empty-quiet">{t('spotlight.empty')}</div>
        )}
        {!inSearchMode && current && (
          <div className={`hero-card-entry ${visible ? 'visible' : 'fading'}`}>
            <div className="hero-card-label">
              <span>{t('hero_card.label_rotating')}</span>
              <span>{selectedLanguage.nativeName}</span>
            </div>
            <div className="hero-card-word">
              {current.lemma}
              {audioUrl && (
                <button
                  type="button"
                  className="hero-card-play"
                  onClick={togglePlay}
                  title={t('hero_card.play')}
                >
                  {playing ? '❚❚' : '▶'} {t('hero_card.play')}
                </button>
              )}
            </div>
            <HeroCardMetaLite item={current} />
            <div className="hero-card-footer">
              <Link className="hero-card-link" to={`/words/${current.id}`}>
                {t('hero_card.view_in_dictionary')} →
              </Link>
              <span className="hero-card-rotctl">
                {index + 1} / {words.length}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function HeroCardMeta({ lexeme }: { lexeme: LexemeWithForms }) {
  const lemmaForm = lexeme.forms?.find((f) => f.is_lemma) ?? lexeme.forms?.[0];
  return (
    <div className="hero-card-ipa">
      {lemmaForm?.ipa_pronunciation ? `/${lemmaForm.ipa_pronunciation}/` : ''}
      {lexeme.part_of_speech && <b>{lexeme.part_of_speech}</b>}
    </div>
  );
}

function HeroCardMetaLite({ item }: { item: WordListItem }) {
  if (!item.part_of_speech) return <div className="hero-card-ipa" aria-hidden />;
  return (
    <div className="hero-card-ipa">
      <b>{item.part_of_speech}</b>
    </div>
  );
}
