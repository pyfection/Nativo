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

export const wordService = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    language_id?: string;
    status_filter?: string;
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
};

export default wordService;

