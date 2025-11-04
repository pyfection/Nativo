/**
 * Document type definitions
 * 
 * Documents group together Text records in multiple languages (translations).
 */

import { Text } from './text';

export interface Document {
  id: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithTexts extends Document {
  texts: Text[];
}

export interface DocumentListItem {
  id: string;
  title: string; // From selected language or primary text
  content_preview: string; // Truncated content
  language_id?: string; // Language of the displayed text
  created_at: string;
  text_count: number; // Number of translations
}

export interface DocumentFilter {
  language_id?: string; // Filter by texts in this language
  search_term?: string; // Search in text titles/content
  created_by_id?: string;
  skip?: number;
  limit?: number;
}

export interface DocumentStatistics {
  total_documents: number;
  documents_with_multiple_languages: number;
  total_texts: number;
  texts_by_language: Record<string, number>;
}

