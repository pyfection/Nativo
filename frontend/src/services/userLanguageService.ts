import api from './api';

export type ProficiencyLevel = 'native' | 'fluent' | 'intermediate' | 'beginner';

export interface JoinLanguageData {
  language_id: string;
  proficiency_level: ProficiencyLevel;
}

export interface UpdateProficiencyData {
  proficiency_level?: ProficiencyLevel;
  can_edit?: boolean;
  can_verify?: boolean;
}

export interface UserLanguageResponse {
  user_id: string;
  language_id: string;
  proficiency_level: ProficiencyLevel;
  can_edit: boolean;
  can_verify: boolean;
  created_at: string;
}

export const userLanguageService = {
  async joinLanguage(userId: string, data: JoinLanguageData): Promise<UserLanguageResponse> {
    const response = await api.post<UserLanguageResponse>(
      `/api/v1/users/${userId}/languages/`,
      data
    );
    return response.data;
  },

  async updateProficiency(
    userId: string,
    languageId: string,
    data: UpdateProficiencyData
  ): Promise<UserLanguageResponse> {
    const response = await api.put<UserLanguageResponse>(
      `/api/v1/users/${userId}/languages/${languageId}`,
      data
    );
    return response.data;
  },

  async leaveLanguage(userId: string, languageId: string): Promise<void> {
    await api.delete(`/api/v1/users/${userId}/languages/${languageId}`);
  },

  async getUserLanguages(userId: string): Promise<UserLanguageResponse[]> {
    const response = await api.get<UserLanguageResponse[]>(
      `/api/v1/users/${userId}/languages/`
    );
    return response.data;
  },
};

export default userLanguageService;

