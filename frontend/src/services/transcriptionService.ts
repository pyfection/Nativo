import { api } from './api';

export interface TranscriptionCandidate {
  word_form_id: string;
  lexeme_id: string;
  form: string;
  lemma: string;
  ipa_pronunciation: string;
  distance: number;
}

export interface TranscriptionToken {
  ipa: string;
  spelling: string;
  known: boolean;
  ambiguous: boolean;
  confidence: number;
  candidates: TranscriptionCandidate[];
}

export interface TranscriptionResult {
  ipa: string;
  text: string;
  tokens: TranscriptionToken[];
  lexicon_size: number;
}

export async function transcribeIpa(languageId: string, ipa: string): Promise<TranscriptionResult> {
  const response = await api.post<TranscriptionResult>('/api/v1/transcribe/ipa', {
    language_id: languageId,
    ipa,
  });
  return response.data;
}

export async function transcribeAudio(languageId: string, audio: Blob): Promise<TranscriptionResult> {
  const form = new FormData();
  form.append('language_id', languageId);
  const ext = audio.type.includes('ogg') ? 'ogg' : audio.type.includes('mp4') ? 'm4a' : 'webm';
  form.append('file', audio, audio instanceof File ? audio.name : `recording.${ext}`);
  const response = await api.post<TranscriptionResult>('/api/v1/transcribe/audio', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}
