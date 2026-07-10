import api from './api';

export type PathState = 'completed' | 'recommended' | 'upcoming';

export type DifficultyRating = 'easy' | 'just_right' | 'challenging' | 'too_hard';

export interface LearningPathEntry {
  text_id: string;
  document_id: string;
  title: string;
  total_lexemes: number;
  new_lexeme_count: number;
  known_pct: number;
  state: PathState;
  completed_at: string | null;
  difficulty_rating: DifficultyRating | null;
}

export interface LexemeKnowledge {
  lexeme_id: string;
  score: number;
}

/** Mirrors KNOWN_SCORE_THRESHOLD on the backend. */
export const KNOWN_SCORE_THRESHOLD = 3;

const learnService = {
  async getPath(languageId: string, limit = 50): Promise<LearningPathEntry[]> {
    const response = await api.get<LearningPathEntry[]>(`/api/v1/learn/${languageId}/path`, {
      params: { limit },
    });
    return response.data;
  },

  async getWordKnowledge(languageId: string): Promise<LexemeKnowledge[]> {
    const response = await api.get<LexemeKnowledge[]>(`/api/v1/learn/${languageId}/words`);
    return response.data;
  },

  /** Tapping a word to look it up is a "don't know yet" signal. */
  async clickWord(lexemeId: string): Promise<LexemeKnowledge> {
    const response = await api.post<LexemeKnowledge>(`/api/v1/learn/words/${lexemeId}/click`);
    return response.data;
  },

  async completeText(
    textId: string,
    difficultyRating: DifficultyRating,
    clickedLexemeIds: string[],
  ): Promise<void> {
    await api.post(`/api/v1/learn/texts/${textId}/complete`, {
      difficulty_rating: difficultyRating,
      clicked_lexeme_ids: clickedLexemeIds,
    });
  },
};

export default learnService;
