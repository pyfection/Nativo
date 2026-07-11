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

export interface ReviewTranslation {
  lemma: string;
  language_id: string;
}

export interface ReviewCard {
  lexeme_id: string;
  lemma: string;
  score: number;
  ipa_pronunciation: string | null;
  lemma_form_id: string | null;
  translations: ReviewTranslation[];
}

export type PlacementLevel = 'beginner' | 'intermediate' | 'advanced';

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

  /** The user's shaky words in a language, weakest first. */
  async getReviewDeck(languageId: string, limit = 20): Promise<ReviewCard[]> {
    const response = await api.get<ReviewCard[]>(`/api/v1/learn/${languageId}/review`, {
      params: { limit },
    });
    return response.data;
  },

  /** Flashcard verdict: knew it (+1) or didn't (-1). */
  async reviewWord(lexemeId: string, knew: boolean): Promise<LexemeKnowledge> {
    const response = await api.post<LexemeKnowledge>(`/api/v1/learn/words/${lexemeId}/review`, {
      knew,
    });
    return response.data;
  },

  /** Seed frequent words as known from a self-assessed starting level. */
  async applyPlacement(languageId: string, level: PlacementLevel): Promise<number> {
    const response = await api.post<{ seeded: number }>(
      `/api/v1/learn/${languageId}/placement`,
      { level },
    );
    return response.data.seeded;
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
