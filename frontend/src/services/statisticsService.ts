import api from './api';

export interface Statistics {
  total_languages: number;
  total_words: number;
  total_audio: number;
  total_documents: number;
  total_contributors: number;
}

export const getStatistics = async (): Promise<Statistics> => {
  const response = await api.get<Statistics>('/api/v1/statistics/');
  return response.data;
};

