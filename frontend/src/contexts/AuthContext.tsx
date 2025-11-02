import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import authService, { User, LoginData, RegisterData } from '../services/authService';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  canEditLanguage: (languageId: string) => boolean;
  canVerifyLanguage: (languageId: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in on mount
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          const currentUser = await authService.getCurrentUser();
          // Fetch language proficiencies
          if (currentUser.id) {
            try {
              const proficiencies = await authService.getUserLanguages(currentUser.id);
              currentUser.language_proficiencies = proficiencies;
            } catch (error) {
              console.error('Failed to load language proficiencies:', error);
              // Continue anyway, user just won't have proficiencies loaded
            }
          }
          setUser(currentUser);
        } catch (error) {
          console.error('Failed to load user:', error);
          authService.logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const login = async (data: LoginData) => {
    await authService.login(data);
    const currentUser = await authService.getCurrentUser();
    // Fetch language proficiencies
    if (currentUser.id) {
      try {
        const proficiencies = await authService.getUserLanguages(currentUser.id);
        currentUser.language_proficiencies = proficiencies;
      } catch (error) {
        console.error('Failed to load language proficiencies:', error);
      }
    }
    setUser(currentUser);
  };

  const register = async (data: RegisterData) => {
    const newUser = await authService.register(data);
    // Auto-login after registration
    await login({ username: data.email, password: data.password });
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const canEditLanguage = (languageId: string): boolean => {
    return authService.canEditLanguage(user, languageId);
  };

  const canVerifyLanguage = (languageId: string): boolean => {
    return authService.canVerifyLanguage(user, languageId);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        canEditLanguage,
        canVerifyLanguage,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

