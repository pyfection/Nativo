import api from './api';

export type ActivityType = 'word_added' | 'text_added' | 'contributor_joined';

export interface ActivityItem {
  type: ActivityType;
  timestamp: string;
  actor: string | null;
  summary: string;
}

export const getActivity = async (
  languageId: string,
  limit = 10
): Promise<ActivityItem[]> => {
  const response = await api.get<ActivityItem[]>('/api/v1/activity/', {
    params: { language_id: languageId, limit },
  });
  return response.data;
};
