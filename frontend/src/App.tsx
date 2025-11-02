import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import './App.css';

// Hardcoded languages with color schemes
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

export const LANGUAGES: Language[] = [
  {
    id: '1',
    name: 'Navajo',
    nativeName: 'Diné bizaad',
    iso: 'nav',
    description: 'Indigenous language of the Navajo people of the Southwestern United States',
    colorScheme: {
      primary: '#8B4513',
      secondary: '#D2691E',
      accent: '#CD853F',
      background: '#FFF8DC',
    },
  },
  {
    id: '2',
    name: 'Hawaiian',
    nativeName: 'ʻŌlelo Hawaiʻi',
    iso: 'haw',
    description: 'Polynesian language of the Hawaiian Islands',
    colorScheme: {
      primary: '#006B8F',
      secondary: '#00A7E1',
      accent: '#4DD0E1',
      background: '#E0F7FA',
    },
  },
  {
    id: '3',
    name: 'Irish',
    nativeName: 'Gaeilge',
    iso: 'gle',
    description: 'Celtic language native to Ireland',
    colorScheme: {
      primary: '#169B62',
      secondary: '#2E7D32',
      accent: '#66BB6A',
      background: '#E8F5E9',
    },
  },
  {
    id: '4',
    name: 'Ainu',
    nativeName: 'アイヌ・イタㇰ',
    iso: 'ain',
    description: 'Language of the indigenous Ainu people of Japan',
    colorScheme: {
      primary: '#7B1FA2',
      secondary: '#9C27B0',
      accent: '#BA68C8',
      background: '#F3E5F5',
    },
  },
  {
    id: '5',
    name: 'Quechua',
    nativeName: 'Runa Simi',
    iso: 'que',
    description: 'Indigenous language family of the Andes',
    colorScheme: {
      primary: '#D32F2F',
      secondary: '#F44336',
      accent: '#EF5350',
      background: '#FFEBEE',
    },
  },
];

function App() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(LANGUAGES[0]);

  return (
    <Router>
      <div className="app" style={{ '--primary': selectedLanguage.colorScheme.primary } as React.CSSProperties}>
        <Routes>
          <Route 
            path="/" 
            element={
              <Home 
                selectedLanguage={selectedLanguage} 
                onLanguageChange={setSelectedLanguage}
                languages={LANGUAGES}
              />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

