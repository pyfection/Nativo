import api from './api';

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface LoginData {
  username: string; // Can be email or username
  password: string;
}

export interface LanguageProficiency {
  language_id: string;
  language_name: string;
  proficiency_level: 'native' | 'fluent' | 'intermediate' | 'beginner';
  can_edit: boolean;
  can_verify: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  language_proficiencies?: LanguageProficiency[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  async register(data: RegisterData): Promise<User> {
    const response = await api.post<User>('/api/v1/auth/register', data);
    return response.data;
  },

  async login(data: LoginData): Promise<TokenResponse> {
    // OAuth2 expects form data
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await api.post<TokenResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Store token
    localStorage.setItem('access_token', response.data.access_token);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me');
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('access_token');
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  async getUserLanguages(userId: string): Promise<LanguageProficiency[]> {
    const response = await api.get<LanguageProficiency[]>(`/api/v1/users/${userId}/languages/`);
    return response.data;
  },

  canEditLanguage(user: User | null, languageId: string): boolean {
    if (!user) return false;
    if (user.role === 'admin') return true;
    
    const proficiency = user.language_proficiencies?.find(
      (lp) => lp.language_id === languageId
    );
    return proficiency?.can_edit || false;
  },

  canVerifyLanguage(user: User | null, languageId: string): boolean {
    if (!user) return false;
    if (user.role === 'admin') return true;
    
    const proficiency = user.language_proficiencies?.find(
      (lp) => lp.language_id === languageId
    );
    return proficiency?.can_verify || false;
  },
};

export default authService;

