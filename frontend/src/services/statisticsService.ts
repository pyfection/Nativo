import api from './api';

export interface Statistics {
  total_languages: number;
  total_words: number;
  total_audio: number;
  total_documents: number;
  total_contributors: number;
}

export const getStatistics = async (languageId?: string): Promise<Statistics> => {
  const params = languageId ? { language_id: languageId } : undefined;
  const response = await api.get<Statistics>('/api/v1/statistics/', { params });
  return response.data;
};
