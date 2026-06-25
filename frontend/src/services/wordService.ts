import api from './api';

// -----------------------------------------------------------------------------
// Lexeme + WordForm types (matches backend/app/schemas/word.py)
// -----------------------------------------------------------------------------

export interface WordForm {
  id: string;
  lexeme_id: string;
  form: string;
  romanization?: string;
  ipa_pronunciation?: string;
  rhyme_key?: string;
  near_rhyme_key?: string;
  is_lemma: boolean;
  plurality?: string;
  grammatical_case?: string;
  verb_aspect?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Lexeme {
  id: string;
  language_id: string;
  lemma: string;
  part_of_speech?: string;
  gender?: string;
  animacy?: string;
  language_register?: string;
  source?: string;
  notes?: string;
  created_by_id: string;
  verified_by_id?: string;
  is_verified: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface LexemeWithForms extends Lexeme {
  forms: WordForm[];
}

export interface LexemeListItem {
  id: string;
  lemma: string;
  language_id: string;
  part_of_speech?: string;
  is_verified: boolean;
  status: string;
  created_at: string;
}

export interface CreateWordFormNested {
  form: string;
  romanization?: string;
  ipa_pronunciation?: string;
  is_lemma?: boolean;
  plurality?: string;
  grammatical_case?: string;
  verb_aspect?: string;
  notes?: string;
  confirmed_at_location_ids?: string[];
}

export interface CreateLexemeData {
  language_id: string;
  lemma: string;
  lemma_form: CreateWordFormNested;
  additional_forms?: CreateWordFormNested[];
  part_of_speech?: string;
  gender?: string;
  animacy?: string;
  language_register?: string;
  source?: string;
  notes?: string;
  tags?: string[];
}

export interface UpdateLexemeData {
  lemma?: string;
  part_of_speech?: string;
  gender?: string;
  animacy?: string;
  language_register?: string;
  source?: string;
  notes?: string;
  status?: string;
  tags?: string[];
}

export interface CreateWordFormData extends CreateWordFormNested {
  lexeme_id: string;
}

export interface UpdateWordFormData {
  form?: string;
  romanization?: string;
  ipa_pronunciation?: string;
  is_lemma?: boolean;
  plurality?: string;
  grammatical_case?: string;
  verb_aspect?: string;
  notes?: string;
  confirmed_at_location_ids?: string[];
}

// -----------------------------------------------------------------------------
// Relations
// -----------------------------------------------------------------------------

export interface LexemeReference {
  id: string;
  lemma: string;
  language_id: string;
  language_name?: string;
  part_of_speech?: string;
}

export interface SynonymLink extends LexemeReference {
  nuance?: string;
  notes?: string;
}

export interface AntonymLink extends LexemeReference {
  antonym_type?: string;
  notes?: string;
}

export interface TranslationLink extends LexemeReference {
  notes?: string;
}

export interface SynonymCreate {
  other_lexeme_id: string;
  nuance?: string;
  notes?: string;
}

export interface AntonymCreate {
  other_lexeme_id: string;
  antonym_type?: string;
  notes?: string;
}

export interface TranslationCreatePayload {
  other_lexeme_id: string;
  notes?: string;
}

export interface TranslationUpdate {
  notes?: string;
}

export interface RhymeMatch {
  word_form_id: string;
  lexeme_id: string;
  form: string;
  lemma: string;
  ipa_pronunciation?: string;
  language_id: string;
}

// -----------------------------------------------------------------------------
// Spelling variants — non-standard spellings that map to a WordForm
// (matches backend/app/schemas/word.py)
// -----------------------------------------------------------------------------

export interface SpellingVariant {
  id: string;
  word_form_id: string;
  variant: string;
  normalized: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSpellingVariantData {
  variant: string;
  note?: string;
}

export interface SpellingCandidate {
  word_form_id: string;
  lexeme_id: string;
  standard_form: string;
  lemma: string;
  note?: string;
}

export interface SpellingResolution {
  token: string;
  normalized: string;
  already_standard: boolean;
  candidates: SpellingCandidate[];
}

// -----------------------------------------------------------------------------
// Back-compat aliases used by some screens during the transition.
// New code should use the Lexeme / WordForm types above.
// -----------------------------------------------------------------------------

export type Word = Lexeme;
export type WordListItem = LexemeListItem;
export type CreateWordData = CreateLexemeData;
export type WordTranslation = TranslationLink;
export interface WordWithTranslations extends LexemeWithForms {
  translations: TranslationLink[];
}
export type TranslationCreate = TranslationCreatePayload;

// -----------------------------------------------------------------------------
// Service
// -----------------------------------------------------------------------------

export const wordService = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    language_id?: string;
    status_filter?: string;
    include_all_statuses?: boolean;
  }): Promise<LexemeListItem[]> {
    const response = await api.get<LexemeListItem[]>('/api/v1/words/', { params });
    return response.data;
  },

  async getById(id: string): Promise<LexemeWithForms> {
    const response = await api.get<LexemeWithForms>(`/api/v1/words/${id}`);
    return response.data;
  },

  async create(data: CreateLexemeData): Promise<LexemeWithForms> {
    const response = await api.post<LexemeWithForms>('/api/v1/words/', data);
    return response.data;
  },

  async update(id: string, data: UpdateLexemeData): Promise<Lexeme> {
    const response = await api.put<Lexeme>(`/api/v1/words/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/words/${id}`);
  },

  async verify(id: string): Promise<Lexeme> {
    const response = await api.post<Lexeme>(`/api/v1/words/${id}/verify`);
    return response.data;
  },

  // Forms
  async listForms(lexemeId: string): Promise<WordForm[]> {
    const response = await api.get<WordForm[]>(`/api/v1/words/${lexemeId}/forms`);
    return response.data;
  },

  async addForm(lexemeId: string, data: CreateWordFormData): Promise<WordForm> {
    const response = await api.post<WordForm>(`/api/v1/words/${lexemeId}/forms`, data);
    return response.data;
  },

  async updateForm(formId: string, data: UpdateWordFormData): Promise<WordForm> {
    const response = await api.put<WordForm>(`/api/v1/words/forms/${formId}`, data);
    return response.data;
  },

  async deleteForm(formId: string): Promise<void> {
    await api.delete(`/api/v1/words/forms/${formId}`);
  },

  // Synonyms / antonyms
  async listSynonyms(lexemeId: string): Promise<SynonymLink[]> {
    const response = await api.get<SynonymLink[]>(`/api/v1/words/${lexemeId}/synonyms`);
    return response.data;
  },

  async addSynonym(lexemeId: string, data: SynonymCreate): Promise<SynonymLink> {
    const response = await api.post<SynonymLink>(`/api/v1/words/${lexemeId}/synonyms`, data);
    return response.data;
  },

  async removeSynonym(lexemeId: string, otherId: string): Promise<void> {
    await api.delete(`/api/v1/words/${lexemeId}/synonyms/${otherId}`);
  },

  async listAntonyms(lexemeId: string): Promise<AntonymLink[]> {
    const response = await api.get<AntonymLink[]>(`/api/v1/words/${lexemeId}/antonyms`);
    return response.data;
  },

  async addAntonym(lexemeId: string, data: AntonymCreate): Promise<AntonymLink> {
    const response = await api.post<AntonymLink>(`/api/v1/words/${lexemeId}/antonyms`, data);
    return response.data;
  },

  async removeAntonym(lexemeId: string, otherId: string): Promise<void> {
    await api.delete(`/api/v1/words/${lexemeId}/antonyms/${otherId}`);
  },

  // Translations
  async listTranslations(lexemeId: string): Promise<TranslationLink[]> {
    const response = await api.get<TranslationLink[]>(`/api/v1/words/${lexemeId}/translations`);
    return response.data;
  },

  async addTranslation(lexemeId: string, data: TranslationCreatePayload): Promise<TranslationLink> {
    const response = await api.post<TranslationLink>(
      `/api/v1/words/${lexemeId}/translations`,
      data,
    );
    return response.data;
  },

  async removeTranslation(lexemeId: string, otherId: string): Promise<void> {
    await api.delete(`/api/v1/words/${lexemeId}/translations/${otherId}`);
  },

  async updateTranslationNotes(
    lexemeId: string,
    otherId: string,
    data: TranslationUpdate,
  ): Promise<TranslationLink> {
    const response = await api.put<TranslationLink>(
      `/api/v1/words/${lexemeId}/translations/${otherId}`,
      data,
    );
    return response.data;
  },

  // Rhymes
  async findRhymes(formId: string, near = false, limit = 50): Promise<RhymeMatch[]> {
    const response = await api.get<RhymeMatch[]>(`/api/v1/words/forms/${formId}/rhymes`, {
      params: { near, limit },
    });
    return response.data;
  },

  // Spelling variants
  async listSpellings(formId: string): Promise<SpellingVariant[]> {
    const response = await api.get<SpellingVariant[]>(`/api/v1/words/forms/${formId}/spellings`);
    return response.data;
  },

  async addSpelling(formId: string, data: CreateSpellingVariantData): Promise<SpellingVariant> {
    const response = await api.post<SpellingVariant>(
      `/api/v1/words/forms/${formId}/spellings`,
      data,
    );
    return response.data;
  },

  async removeSpelling(variantId: string): Promise<void> {
    await api.delete(`/api/v1/words/spellings/${variantId}`);
  },

  async resolveSpelling(languageId: string, token: string): Promise<SpellingResolution> {
    const response = await api.get<SpellingResolution>('/api/v1/words/spellings/resolve', {
      params: { language_id: languageId, token },
    });
    return response.data;
  },

  // Search
  async search(params: {
    q: string;
    language_ids?: string;
    include_unpublished?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<LexemeWithForms[]> {
    const response = await api.get<LexemeWithForms[]>('/api/v1/words/search', { params });
    return response.data;
  },
};

export default wordService;
