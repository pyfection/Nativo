import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AppLayout from './components/layouts/AppLayout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Languages from './pages/Languages';
import WordList from './pages/WordList';
import AddWord from './pages/AddWord';
import Dictionary from './pages/Dictionary';
import DocumentList from './pages/DocumentList';
import AddDocument from './pages/AddDocument';
import languageService, { LanguageResponse } from './services/languageService';
import './App.css';

// Frontend Language type with color scheme
export interface Language {
  id: string;
  name: string;
  nativeName: string;
  iso: string;
  description: string;
  managed: boolean;
  colorScheme: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
  };
}

// Default color scheme for languages without colors
const DEFAULT_COLOR_SCHEME = {
  primary: '#8B4513',
  secondary: '#D2691E',
  accent: '#CD853F',
  background: '#FFF8DC',
};

// Convert API language to frontend Language type
function convertLanguage(apiLang: LanguageResponse): Language {
  return {
    id: apiLang.id,
    name: apiLang.name,
    nativeName: apiLang.native_name || apiLang.name,
    iso: apiLang.iso_639_3 || '',
    description: apiLang.description || '',
    managed: apiLang.managed,
    colorScheme: {
      primary: apiLang.primary_color || DEFAULT_COLOR_SCHEME.primary,
      secondary: apiLang.secondary_color || DEFAULT_COLOR_SCHEME.secondary,
      accent: apiLang.accent_color || DEFAULT_COLOR_SCHEME.accent,
      background: apiLang.background_color || DEFAULT_COLOR_SCHEME.background,
    },
  };
}

const SELECTED_LANGUAGE_KEY = 'nativo_selected_language_id';

function App() {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch languages on mount
  useEffect(() => {
    const fetchLanguages = async () => {
      try {
        setLoading(true);
        // First get the list of languages
        const languageList = await languageService.getAll();
        
        // Then fetch full details for each language (to get colors)
        const languagesWithDetails = await Promise.all(
          languageList.map(lang => languageService.getById(lang.id))
        );
        
        // Convert to frontend format
        const convertedLanguages = languagesWithDetails.map(convertLanguage);
        setLanguages(convertedLanguages);
        
        // Try to restore previously selected language from localStorage
        const savedLanguageId = localStorage.getItem(SELECTED_LANGUAGE_KEY);
        let languageToSelect = convertedLanguages[0]; // Default to first language
        
        if (savedLanguageId) {
          const savedLanguage = convertedLanguages.find(lang => lang.id === savedLanguageId);
          if (savedLanguage) {
            languageToSelect = savedLanguage;
          }
        }
        
        if (languageToSelect) {
          setSelectedLanguage(languageToSelect);
        }
      } catch (err) {
        console.error('Failed to fetch languages:', err);
        setError('Failed to load languages');
      } finally {
        setLoading(false);
      }
    };

    fetchLanguages();
  }, []);

  // Save selected language to localStorage whenever it changes
  useEffect(() => {
    if (selectedLanguage) {
      localStorage.setItem(SELECTED_LANGUAGE_KEY, selectedLanguage.id);
    }
  }, [selectedLanguage]);

  // Show loading state
  if (loading) {
    return (
      <div className="app-loading" style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="loading-spinner"></div>
        <p>Loading languages...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="app-error" style={{ padding: '2rem', textAlign: 'center' }}>
        <h2>Error</h2>
        <p>{error}</p>
        <p style={{ fontSize: '0.875rem', color: '#666' }}>Make sure the backend is running on http://localhost:8000</p>
        <button onClick={() => window.location.reload()} style={{ marginTop: '1rem', padding: '0.5rem 1rem', cursor: 'pointer' }}>Retry</button>
      </div>
    );
  }

  // Show message if no languages found
  if (languages.length === 0) {
    return (
      <div className="app-empty" style={{ padding: '2rem', textAlign: 'center' }}>
        <h2>No Languages Found</h2>
        <p>No endangered languages have been added to the database yet.</p>
      </div>
    );
  }

  return (
    <Router>
      <AuthProvider>
        <div className="app" style={{ '--primary': selectedLanguage?.colorScheme.primary } as React.CSSProperties}>
          <Routes>
            <Route 
              path="/" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <Home 
                    selectedLanguage={selectedLanguage!} 
                    onLanguageChange={setSelectedLanguage}
                    languages={languages}
                  />
                </AppLayout>
              } 
            />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Languages Route */}
            <Route 
              path="/languages" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <Languages />
                </AppLayout>
              } 
            />
            
            {/* Word Routes */}
            <Route 
              path="/words" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <WordList selectedLanguage={selectedLanguage!} />
                </AppLayout>
              } 
            />
            <Route 
              path="/words/add" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <AddWord selectedLanguage={selectedLanguage!} />
                </AppLayout>
              } 
            />
            
            {/* Dictionary Route */}
            <Route 
              path="/dictionary" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <Dictionary 
                    selectedLanguage={selectedLanguage!}
                    languages={languages}
                  />
                </AppLayout>
              } 
            />
            
            {/* Document Routes */}
            <Route 
              path="/documents" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <DocumentList selectedLanguage={selectedLanguage!} />
                </AppLayout>
              } 
            />
            <Route 
              path="/documents/add" 
              element={
                <AppLayout
                  selectedLanguage={selectedLanguage!}
                  onLanguageChange={setSelectedLanguage}
                  languages={languages}
                >
                  <AddDocument />
                </AppLayout>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;

