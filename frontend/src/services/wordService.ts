import api from './api';

export interface Word {
  id: string;
  word: string;
  language_id: string;
  romanization?: string;
  ipa_pronunciation?: string;
  part_of_speech?: string;
  definition: string;
  literal_translation?: string;
  context_notes?: string;
  usage_examples?: string;
  status: string;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface WordListItem {
  id: string;
  word: string;
  language_id: string;
  part_of_speech?: string;
  definition: string;
  status: string;
}

export interface CreateWordData {
  word: string;
  language_id: string;
  romanization?: string;
  ipa_pronunciation?: string;
  part_of_speech?: string;
  definition: string;
  literal_translation?: string;
  context_notes?: string;
  usage_examples?: string;
}

export interface WordTranslation {
  id: string;
  word: string;
  romanization?: string;
  language_id: string;
  language_name?: string;
  part_of_speech?: string;
  notes?: string;
}

export interface WordWithTranslations extends Word {
  translations: WordTranslation[];
}

export interface TranslationCreate {
  translation_id: string;
  notes?: string;
}

export interface TranslationUpdate {
  notes?: string;
}

export const wordService = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    language_id?: string;
    status_filter?: string;
    include_all_statuses?: boolean;
  }): Promise<WordListItem[]> {
    const response = await api.get<WordListItem[]>('/api/v1/words/', { params });
    return response.data;
  },

  async getById(id: string): Promise<Word> {
    const response = await api.get<Word>(`/api/v1/words/${id}`);
    return response.data;
  },

  async create(data: CreateWordData): Promise<Word> {
    const response = await api.post<Word>('/api/v1/words/', data);
    return response.data;
  },

  async update(id: string, data: Partial<CreateWordData>): Promise<Word> {
    const response = await api.put<Word>(`/api/v1/words/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/words/${id}`);
  },

  async verify(id: string): Promise<Word> {
    const response = await api.post<Word>(`/api/v1/words/${id}/verify`);
    return response.data;
  },

  // Translation management
  async addTranslation(wordId: string, data: TranslationCreate): Promise<Word> {
    const response = await api.post<Word>(`/api/v1/words/${wordId}/translations/`, data);
    return response.data;
  },

  async removeTranslation(wordId: string, translationId: string): Promise<void> {
    await api.delete(`/api/v1/words/${wordId}/translations/${translationId}`);
  },

  async updateTranslationNotes(wordId: string, translationId: string, data: TranslationUpdate): Promise<Word> {
    const response = await api.put<Word>(`/api/v1/words/${wordId}/translations/${translationId}`, data);
    return response.data;
  },

  // Dictionary search
  async search(params: {
    q: string;
    language_ids?: string;  // Comma-separated language IDs
    include_translations?: boolean;
    include_unpublished?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<WordWithTranslations[]> {
    const response = await api.get<WordWithTranslations[]>('/api/v1/words/search', { params });
    return response.data;
  },
};

export default wordService;

