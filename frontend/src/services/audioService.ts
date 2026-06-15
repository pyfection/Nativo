import api, { API_URL } from './api';

export interface AudioListItem {
  id: string;
  file_path: string;
  file_size: number | null;
  duration: number | null;
  mime_type: string | null;
  uploaded_by_id: string;
  uploader_username: string | null;
  created_at: string;
  word_count: number;
}

export interface UploadedAudio {
  id: string;
  file_path: string;
  file_size: number | null;
  duration: number | null;
  mime_type: string | null;
  word_form_id?: string | null;
}

/**
 * Resolve a stored `file_path` (root-relative like "/uploads/audio/…") to a
 * fully-qualified URL fetchable from the browser. Same value works in dev
 * and prod — only the API origin differs.
 */
export function fullAudioUrl(filePath: string): string {
  if (/^https?:/i.test(filePath)) return filePath;
  return `${API_URL.replace(/\/$/, '')}${filePath}`;
}

export const listAudio = async (languageId?: string, limit = 50): Promise<AudioListItem[]> => {
  const params: Record<string, string | number> = { limit };
  if (languageId) params.language_id = languageId;
  const response = await api.get<AudioListItem[]>('/api/v1/audio/', { params });
  return response.data;
};

export const listAudioForForm = async (wordFormId: string): Promise<AudioListItem[]> => {
  const response = await api.get<AudioListItem[]>(`/api/v1/audio/by-form/${wordFormId}`);
  return response.data;
};

export const uploadAudio = async (
  blob: Blob,
  opts: {
    wordFormId?: string;
    durationSeconds?: number | null;
    isPrimary?: boolean;
    filename?: string;
  } = {},
): Promise<UploadedAudio> => {
  const form = new FormData();
  // MediaRecorder blobs are unnamed; passing a descriptive filename makes
  // server logs readable. The server still routes by Content-Type.
  const filename = opts.filename ?? `recording-${Date.now()}.webm`;
  form.append('file', blob, filename);
  if (opts.wordFormId) form.append('word_form_id', opts.wordFormId);
  if (opts.durationSeconds != null && Number.isFinite(opts.durationSeconds)) {
    form.append('duration', String(Math.round(opts.durationSeconds)));
  }
  if (opts.isPrimary) form.append('is_primary', 'true');
  const response = await api.post<UploadedAudio>('/api/v1/audio/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const deleteAudio = async (audioId: string): Promise<void> => {
  await api.delete(`/api/v1/audio/${audioId}`);
};
