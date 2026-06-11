import api from './api';

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

export const listAudio = async (languageId?: string, limit = 50): Promise<AudioListItem[]> => {
  const params: Record<string, string | number> = { limit };
  if (languageId) params.language_id = languageId;
  const response = await api.get<AudioListItem[]>('/api/v1/audio/', { params });
  return response.data;
};
