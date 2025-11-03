import api from './api';

export interface LanguageResponse {
  id: string;
  name: string;
  native_name: string | null;
  iso_639_3: string | null;
  description: string | null;
  is_endangered: boolean;
  managed: boolean;
  primary_color: string | null;
  secondary_color: string | null;
  accent_color: string | null;
  background_color: string | null;
  created_at: string;
  updated_at: string;
}

export interface LanguageListItem {
  id: string;
  name: string;
  native_name: string | null;
  iso_639_3: string | null;
  is_endangered: boolean;
  managed: boolean;
}

export interface CreateLanguageData {
  name: string;
  native_name?: string;
  iso_639_3?: string;
  description?: string;
  is_endangered?: boolean;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
}

export const languageService = {
  async getAll(params?: { skip?: number; limit?: number; is_endangered?: boolean }): Promise<LanguageListItem[]> {
    const response = await api.get<LanguageListItem[]>('/api/v1/languages/', { params });
    return response.data;
  },

  async getById(id: string): Promise<LanguageResponse> {
    const response = await api.get<LanguageResponse>(`/api/v1/languages/${id}`);
    return response.data;
  },

  async create(data: CreateLanguageData): Promise<LanguageResponse> {
    const response = await api.post<LanguageResponse>('/api/v1/languages/', data);
    return response.data;
  },

  async update(id: string, data: Partial<CreateLanguageData>): Promise<LanguageResponse> {
    const response = await api.put<LanguageResponse>(`/api/v1/languages/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/languages/${id}`);
  },
};

export default languageService;

