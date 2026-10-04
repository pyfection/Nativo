import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Language } from '../App';
import { useAuth } from '../contexts/AuthContext';
import {
  TranscriptionResult,
  transcribeAudio,
  transcribeIpa,
} from '../services/transcriptionService';
import { languageDisplayName } from '../utils/languageName';
import './Transcribe.css';

// Mirrors the backend: the first word of the result is capitalised.
const capitalizeFirst = (word: string) => word.charAt(0).toUpperCase() + word.slice(1);

interface TranscribeProps {
  selectedLanguage: Language;
}

type Status = 'idle' | 'recording' | 'working';

/**
 * Speech / IPA → standard spelling (phase 1 prototype).
 *
 * Audio goes to POST /api/v1/transcribe/audio (zero-shot phoneme recogniser,
 * then lexicon matching); typed IPA goes to POST /api/v1/transcribe/ipa. The
 * recognised IPA is put back in the IPA box so a listener can correct it and
 * re-run. Every word stays editable — the result is a suggestion, not saved.
 */
export default function Transcribe({ selectedLanguage }: TranscribeProps) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [ipa, setIpa] = useState('');
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [words, setWords] = useState<string[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  // Set on unmount so a recording stopped by navigation isn't sent off.
  const discardRef = useRef(false);

  const canRecord = typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices;

  // Stop the mic if the page unmounts mid-recording.
  useEffect(() => {
    return () => {
      discardRef.current = true;
      const recorder = recorderRef.current;
      if (recorder && recorder.state !== 'inactive') recorder.stop();
      recorder?.stream.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const showResult = (data: TranscriptionResult) => {
    setResult(data);
    setWords(data.tokens.map((token) => token.spelling));
    setCopied(false);
  };

  const showError = (err: any, fallbackKey: string) => {
    const detail = err.response?.data?.detail;
    setError(typeof detail === 'string' ? detail : t(fallbackKey));
  };

  const runIpa = async () => {
    if (!ipa.trim()) return;
    setStatus('working');
    setError('');
    try {
      showResult(await transcribeIpa(selectedLanguage.id, ipa.trim()));
    } catch (err: any) {
      showError(err, 'transcribe_page.error_transcribe');
    } finally {
      setStatus('idle');
    }
  };

  const runAudio = async (audio: Blob) => {
    setStatus('working');
    setError('');
    try {
      const data = await transcribeAudio(selectedLanguage.id, audio);
      setIpa(data.ipa);
      showResult(data);
    } catch (err: any) {
      showError(err, 'transcribe_page.error_transcribe');
    } finally {
      setStatus('idle');
    }
  };

  const startRecording = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        if (discardRef.current) return;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        void runAudio(blob);
      };
      recorderRef.current = recorder;
      recorder.start();
      setStatus('recording');
    } catch (err: any) {
      setError(
        err.name === 'NotAllowedError'
          ? t('audio_recorder.mic_access_denied')
          : t('audio_recorder.could_not_start'),
      );
    }
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (file) void runAudio(file);
  };

  const setWord = (index: number, value: string) => {
    setWords((prev) => prev.map((w, i) => (i === index ? value : w)));
    setCopied(false);
  };

  const finalText = words.filter((w) => w.trim()).join(' ');

  const copyText = async () => {
    try {
      await navigator.clipboard.writeText(finalText);
      setCopied(true);
    } catch {
      // Clipboard can be blocked (insecure context); the text is still selectable.
    }
  };

  const busy = status !== 'idle';

  return (
    <div className="transcribe-page">
      <div className="transcribe-header">
        <h1>{t('transcribe_page.title')}</h1>
        <p className="subtitle">
          {t('transcribe_page.subtitle', { language: languageDisplayName(selectedLanguage) })}
        </p>
      </div>

      <section className="transcribe-panel">
        <h2>{t('transcribe_page.audio_heading')}</h2>
        {isAuthenticated ? (
          <div className="transcribe-audio-actions">
            {status === 'recording' ? (
              <button type="button" className="transcribe-button recording" onClick={stopRecording}>
                ■ {t('transcribe_page.stop')}
              </button>
            ) : (
              <button
                type="button"
                className="transcribe-button"
                onClick={startRecording}
                disabled={busy || !canRecord}
              >
                ● {t('transcribe_page.record')}
              </button>
            )}
            <label className={`transcribe-button secondary ${busy ? 'disabled' : ''}`}>
              {t('transcribe_page.upload')}
              <input type="file" accept="audio/*" onChange={handleFile} disabled={busy} hidden />
            </label>
          </div>
        ) : (
          <p className="transcribe-hint">
            <Link to="/login">{t('transcribe_page.sign_in')}</Link> {t('transcribe_page.sign_in_post')}
          </p>
        )}
        <p className="transcribe-hint">{t('transcribe_page.audio_hint')}</p>
      </section>

      <section className="transcribe-panel">
        <h2>{t('transcribe_page.ipa_heading')}</h2>
        <textarea
          className="transcribe-ipa"
          value={ipa}
          onChange={(e) => setIpa(e.target.value)}
          placeholder="miɐ san haɪt dahɔɐm"
          rows={2}
          maxLength={300}
          spellCheck={false}
        />
        <button
          type="button"
          className="transcribe-button"
          onClick={runIpa}
          disabled={busy || !ipa.trim()}
        >
          {status === 'working' ? t('transcribe_page.working') : t('transcribe_page.transcribe')}
        </button>
      </section>

      {error && <div className="error-message">{error}</div>}

      {result && !error && (
        <section className="transcribe-panel transcribe-result">
          <h2>{t('transcribe_page.result_heading')}</h2>
          {result.lexicon_size === 0 && (
            <p className="transcribe-hint">{t('transcribe_page.empty_lexicon')}</p>
          )}
          <div className="transcribe-tokens">
            {result.tokens.map((token, i) => {
              const title = `/${token.ipa}/ · ${
                token.known
                  ? t('transcribe_page.confidence', { pct: Math.round(token.confidence * 100) })
                  : t('transcribe_page.unknown')
              }`;
              const cls = `transcribe-token ${token.known ? '' : 'unknown'} ${
                token.ambiguous ? 'ambiguous' : ''
              } ${token.known && token.confidence < 0.6 ? 'low' : ''}`;
              const firstWord = result.tokens.findIndex((t) => t.spelling) === i;
              const spellings = Array.from(
                new Set(
                  token.candidates.map((c) => (firstWord ? capitalizeFirst(c.form) : c.form)),
                ),
              );
              return spellings.length > 1 ? (
                <select
                  key={i}
                  className={cls}
                  title={title}
                  value={words[i]}
                  onChange={(e) => setWord(i, e.target.value)}
                >
                  {spellings.map((form) => (
                    <option key={form} value={form}>
                      {form}
                    </option>
                  ))}
                  {!spellings.includes(words[i]) && <option value={words[i]}>{words[i]}</option>}
                </select>
              ) : (
                <input
                  key={i}
                  className={cls}
                  title={title}
                  value={words[i] ?? ''}
                  size={Math.max(2, (words[i] ?? '').length)}
                  onChange={(e) => setWord(i, e.target.value)}
                />
              );
            })}
          </div>
          <p className="transcribe-legend">
            <span className="transcribe-token unknown">abc</span> {t('transcribe_page.legend_unknown')}
            <span className="transcribe-token low">abc</span> {t('transcribe_page.legend_low')}
          </p>
          <div className="transcribe-final">
            <p>{finalText}</p>
            <button type="button" className="transcribe-button secondary" onClick={copyText}>
              {copied ? t('transcribe_page.copied') : t('transcribe_page.copy')}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
