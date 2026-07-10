import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { useAuth } from '../../contexts/AuthContext';
import {
  AudioListItem,
  deleteAudio,
  fullAudioUrl,
  listAudioForForm,
  uploadAudio,
} from '../../services/audioService';
import './AudioRecorder.css';

interface AudioRecorderProps {
  /** WordForm to upload-and-link audio against. */
  wordFormId: string;
  /** True if the current user can record/delete audio on this form. */
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
 * Per-WordForm voice recorder.
 *
 * Uses the browser MediaRecorder API to capture audio (webm/opus by default)
 * and uploads in one round-trip to /api/v1/audio/upload with the
 * word_form_id pre-filled. Existing recordings render as inline players with
 * a per-row delete control.
 *
 * No file-picker fallback yet — that's a phase D nicety.
 */
export default function AudioRecorder({
  wordFormId,
  canEdit,
  onChange,
  onError,
  onMessage,
}: AudioRecorderProps) {
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

  // Initial load + reset on form change.
  useEffect(() => {
    let cancelled = false;
    setAudios([]);
    listAudioForForm(wordFormId)
      .then((data) => {
        if (!cancelled) {
          setAudios(data);
          onChange?.(data);
        }
      })
      .catch(() => {
        // Form may have no audio rows; treat as empty rather than error.
        if (!cancelled) setAudios([]);
      });
    return () => {
      cancelled = true;
    };
  }, [wordFormId, onChange]);

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
            durationSeconds: duration,
            isPrimary: audios.length === 0,
          });
          // Refresh from server so we get the canonical Audio rows (with
          // file_path) rather than constructing optimistically.
          const refreshed = await listAudioForForm(wordFormId);
          setAudios(refreshed);
          onChange?.(refreshed);
          onMessage?.('Recording uploaded.');
        } catch (err: any) {
          onError?.(err.response?.data?.detail || 'Upload failed');
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
          ? 'Microphone access denied. Allow it in your browser settings to record.'
          : 'Could not start recording.',
      );
    }
  };

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  };

  const handleDelete = async (audio: AudioListItem) => {
    if (!window.confirm('Delete this recording?')) return;
    try {
      await deleteAudio(audio.id);
      const refreshed = audios.filter((a) => a.id !== audio.id);
      setAudios(refreshed);
      onChange?.(refreshed);
      onMessage?.('Recording deleted.');
    } catch (err: any) {
      onError?.(err.response?.data?.detail || 'Failed to delete recording.');
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
                title="Record a pronunciation for this form using your microphone."
              >
                {status === 'uploading' ? 'Uploading…' : '● Record'}
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-ghost btn-sm audio-recorder-stop"
                onClick={stopRecording}
                title="Stop recording and upload."
              >
                ■ Stop ({elapsed.toFixed(1)}s)
              </button>
            )}
          </>
        )}
        {unsupported && (
          <span className="audio-recorder-unsupported">
            Recording isn't supported in this browser.
          </span>
        )}
        {/* The moment read-only runs out is the moment to invite a signup:
            a guest looking at a form nobody has recorded yet. */}
        {!isAuthenticated && audios.length === 0 && (
          <Link to="/register" state={{ from: location }} className="audio-recorder-guest-cta">
            No recording yet — sign up to lend your voice
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
                  <span className="audio-recorder-duration">{audio.duration}s</span>
                )}
                {audio.uploader_username && (
                  <span className="audio-recorder-uploader">
                    by {audio.uploader_username}
                  </span>
                )}
              </div>
              {canEdit && (
                <button
                  type="button"
                  className="btn btn-ghost btn-xs"
                  onClick={() => handleDelete(audio)}
                  title="Delete this recording"
                >
                  Delete
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
