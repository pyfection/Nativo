import api from './api';

export interface ContributorItem {
  id: string;
  username: string;
  role: string;
  proficiency_level: string | null;
  word_count: number;
  text_count: number;
}

export const listContributors = async (
  languageId?: string,
  limit = 50
): Promise<ContributorItem[]> => {
  const params: Record<string, string | number> = { limit };
  if (languageId) params.language_id = languageId;
  const response = await api.get<ContributorItem[]>('/api/v1/contributors/', { params });
  return response.data;
};
