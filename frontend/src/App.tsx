import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import AppLayout from './components/layouts/AppLayout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import WordList from './pages/WordList';
import AddWord from './pages/AddWord';
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
    colorScheme: {
      primary: apiLang.primary_color || DEFAULT_COLOR_SCHEME.primary,
      secondary: apiLang.secondary_color || DEFAULT_COLOR_SCHEME.secondary,
      accent: apiLang.accent_color || DEFAULT_COLOR_SCHEME.accent,
      background: apiLang.background_color || DEFAULT_COLOR_SCHEME.background,
    },
  };
}

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
        
        // Set first language as selected
        if (convertedLanguages.length > 0) {
          setSelectedLanguage(convertedLanguages[0]);
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

  // Show loading state
  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading languages...</p>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="app-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // Show message if no languages found
  if (languages.length === 0) {
    return (
      <div className="app-empty">
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
                  <AddWord />
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

