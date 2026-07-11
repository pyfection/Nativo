import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../../contexts/AuthContext';
import {
  AudioListItem,
  deleteAudio,
  fullAudioUrl,
  listAudioForForm,
  listAudioForText,
  uploadAudio,
} from '../../services/audioService';
import './AudioRecorder.css';

interface AudioRecorderProps {
  /** WordForm to upload-and-link audio against (pronunciation mode). */
  wordFormId?: string;
  /** Text to attach narration to (narration mode). Provide exactly one target. */
  textId?: string;
  /** True if the current user can record/delete audio on this target. */
  canEdit: boolean;
  /** Called whenever the list of attached recordings changes. */
  onChange?: (audios: AudioListItem[]) => void;
  /** Surface upload errors to the parent (which renders the toast stack). */
  onError?: (msg: string) => void;
  /** Surface success messages similarly. */
  onMessage?: (msg: string) => void;
}

type Status = 'idle' | 'recording' | 'uploading';

/**
 * Voice recorder for a WordForm (pronunciation) or a Text (narration).
 *
 * Uses the browser MediaRecorder API to capture audio (webm/opus by default)
 * and uploads in one round-trip to /api/v1/audio/upload with the target id
 * pre-filled. Existing recordings render as inline players with a per-row
 * delete control.
 *
 * No file-picker fallback yet — that's a phase D nicety.
 */
export default function AudioRecorder({
  wordFormId,
  textId,
  canEdit,
  onChange,
  onError,
  onMessage,
}: AudioRecorderProps) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const [audios, setAudios] = useState<AudioListItem[]>([]);
  const [status, setStatus] = useState<Status>('idle');
  const [elapsed, setElapsed] = useState(0);
  const [unsupported, setUnsupported] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const elapsedTimerRef = useRef<number | null>(null);
  const startedAtRef = useRef<number | null>(null);

  // Initial load + reset on target change.
  useEffect(() => {
    let cancelled = false;
    setAudios([]);
    const fetchList = textId
      ? listAudioForText(textId)
      : wordFormId
        ? listAudioForForm(wordFormId)
        : Promise.resolve<AudioListItem[]>([]);
    fetchList
      .then((data) => {
        if (!cancelled) {
          setAudios(data);
          onChange?.(data);
        }
      })
      .catch(() => {
        // Target may have no audio rows; treat as empty rather than error.
        if (!cancelled) setAudios([]);
      });
    return () => {
      cancelled = true;
    };
  }, [wordFormId, textId, onChange]);

  // Feature detect on mount.
  useEffect(() => {
    if (!navigator.mediaDevices || typeof MediaRecorder === 'undefined') {
      setUnsupported(true);
    }
  }, []);

  // Clean up if the component unmounts mid-recording.
  useEffect(() => {
    return () => {
      stopElapsed();
      recorderRef.current?.state !== 'inactive' && recorderRef.current?.stop();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startElapsed = () => {
    startedAtRef.current = performance.now();
    setElapsed(0);
    elapsedTimerRef.current = window.setInterval(() => {
      if (startedAtRef.current != null) {
        setElapsed((performance.now() - startedAtRef.current) / 1000);
      }
    }, 200);
  };
  const stopElapsed = () => {
    if (elapsedTimerRef.current != null) {
      clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
  };

  const startRecording = async () => {
    if (unsupported) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      // Prefer webm/opus, fall back to whatever the browser supports.
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : '';
      const recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stopElapsed();
        const duration =
          startedAtRef.current != null
            ? (performance.now() - startedAtRef.current) / 1000
            : null;
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });
        chunksRef.current = [];
        setStatus('uploading');
        try {
          await uploadAudio(blob, {
            wordFormId,
            textId,
            durationSeconds: duration,
            // is_primary is a word-form concept; irrelevant for narration.
            isPrimary: wordFormId ? audios.length === 0 : false,
          });
          // Refresh from server so we get the canonical Audio rows (with
          // file_path) rather than constructing optimistically.
          const refreshed = textId
            ? await listAudioForText(textId)
            : await listAudioForForm(wordFormId!);
          setAudios(refreshed);
          onChange?.(refreshed);
          onMessage?.(t('audio_recorder.recording_uploaded'));
        } catch (err: any) {
          onError?.(err.response?.data?.detail || t('audio_recorder.upload_failed'));
        } finally {
          setStatus('idle');
          setElapsed(0);
          startedAtRef.current = null;
        }
      };
      recorderRef.current = recorder;
      recorder.start();
      setStatus('recording');
      startElapsed();
    } catch (err: any) {
      onError?.(
        err.name === 'NotAllowedError'
          ? t('audio_recorder.mic_access_denied')
          : t('audio_recorder.could_not_start'),
      );
    }
  };

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  };

  const handleDelete = async (audio: AudioListItem) => {
    if (!window.confirm(t('audio_recorder.confirm_delete'))) return;
    try {
      await deleteAudio(audio.id);
      const refreshed = audios.filter((a) => a.id !== audio.id);
      setAudios(refreshed);
      onChange?.(refreshed);
      onMessage?.(t('audio_recorder.recording_deleted'));
    } catch (err: any) {
      onError?.(err.response?.data?.detail || t('audio_recorder.delete_failed'));
    }
  };

  return (
    <div className="audio-recorder">
      <div className="audio-recorder-controls">
        {canEdit && !unsupported && (
          <>
            {status !== 'recording' ? (
              <button
                type="button"
                className="btn btn-accent btn-sm"
                onClick={startRecording}
                disabled={status === 'uploading'}
                title={t('audio_recorder.record_button_title')}
              >
                {status === 'uploading' ? t('audio_recorder.uploading') : t('audio_recorder.record')}
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-ghost btn-sm audio-recorder-stop"
                onClick={stopRecording}
                title={t('audio_recorder.stop_button_title')}
              >
                {t('audio_recorder.stop', { s: elapsed.toFixed(1) })}
              </button>
            )}
          </>
        )}
        {unsupported && (
          <span className="audio-recorder-unsupported">
            {t('audio_recorder.unsupported')}
          </span>
        )}
        {/* The moment read-only runs out is the moment to invite a signup:
            a guest looking at a form nobody has recorded yet. */}
        {!isAuthenticated && audios.length === 0 && (
          <Link to="/register" state={{ from: location }} className="audio-recorder-guest-cta">
            {t('audio_recorder.guest_cta')}
          </Link>
        )}
      </div>

      {audios.length > 0 && (
        <ul className="audio-recorder-list">
          {audios.map((audio) => (
            <li key={audio.id} className="audio-recorder-row">
              <audio
                controls
                preload="metadata"
                src={fullAudioUrl(audio.file_path)}
                className="audio-recorder-player"
              />
              <div className="audio-recorder-row-meta">
                {audio.duration != null && (
                  <span className="audio-recorder-duration">
                    {t('audio_recorder.duration_seconds', { s: audio.duration })}
                  </span>
                )}
                {audio.uploader_username && (
                  <span className="audio-recorder-uploader">
                    {t('audio_recorder.by_uploader', { username: audio.uploader_username })}
                  </span>
                )}
              </div>
              {canEdit && (
                <button
                  type="button"
                  className="btn btn-ghost btn-xs"
                  onClick={() => handleDelete(audio)}
                  title={t('audio_recorder.delete_button_title')}
                >
                  {t('audio_recorder.delete')}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
