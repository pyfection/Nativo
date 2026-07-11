import api from './api';

export type ActivityType = 'word_added' | 'text_added' | 'contributor_joined';

export interface ActivityItem {
  type: ActivityType;
  timestamp: string;
  actor: string | null;
  /** English fallback line; clients localize from subject/detail. */
  summary: string;
  /** The lemma/title/username the event is about. */
  subject: string | null;
  /** Proficiency level for contributor_joined. */
  detail: string | null;
  /** Lexeme id for word_added, Document id for text_added, null otherwise. */
  entity_id: string | null;
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
