/**
 * Text type definitions
 * 
 * Texts contain actual content in specific languages.
 * Multiple Texts can belong to the same Document (translations).
 */

export enum DocumentType {
  // Full documents
  STORY = 'story',
  HISTORICAL_RECORD = 'historical_record',
  BOOK = 'book',
  ARTICLE = 'article',
  TRANSCRIPTION = 'transcription',
  
  // Text snippets
  DEFINITION = 'definition',
  LITERAL_TRANSLATION = 'literal_translation',
  CONTEXT_NOTE = 'context_note',
  USAGE_EXAMPLE = 'usage_example',
  ETYMOLOGY = 'etymology',
  CULTURAL_SIGNIFICANCE = 'cultural_significance',
  TRANSLATION = 'translation',
  NOTE = 'note',
  
  OTHER = 'other',
}

export enum TextWordLinkStatus {
  SUGGESTED = 'suggested',
  CONFIRMED = 'confirmed',
  REJECTED = 'rejected',
}

export interface TextWordLink {
  id: string;
  text_id: string;
  word_id: string;
  start_char: number;
  end_char: number;
  status: TextWordLinkStatus;
  confidence?: number | null;
  notes?: string | null;
  created_by_id?: string | null;
  verified_by_id?: string | null;
  created_at: string;
  updated_at: string;
  verified_at?: string | null;
  word_text?: string | null;
  word_language_id?: string | null;
}

export interface TextWordLinkCreate {
  word_id: string;
  start_char: number;
  end_char: number;
  status?: TextWordLinkStatus;
  notes?: string;
}

export interface TextWordLinkUpdate {
  status?: TextWordLinkStatus;
  notes?: string;
  word_id?: string;
}

export interface Text {
  id: string;
  title: string;
  content: string;
  document_type: DocumentType;
  language_id?: string;
  document_id?: string;
  is_primary: boolean;
  source?: string;
  notes?: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
  word_links?: TextWordLink[];
}

export interface TextListItem {
  id: string;
  title: string;
  content: string; // May be truncated
  document_type: DocumentType;
  language_id?: string;
  document_id?: string;
  is_primary: boolean;
  created_at: string;
}

export interface TextWithLinks extends Text {
  word_links: TextWordLink[];
}

export interface TextCreate {
  title: string;
  content: string;
  document_type: DocumentType;
  language_id?: string;
  document_id?: string;
  is_primary?: boolean;
  source?: string;
  notes?: string;
}

export interface TextUpdate {
  title?: string;
  content?: string;
  document_type?: DocumentType;
  language_id?: string;
  document_id?: string;
  is_primary?: boolean;
  source?: string;
  notes?: string;
}

export interface TextFilter {
  document_type?: DocumentType;
  language_id?: string;
  document_id?: string;
  is_primary?: boolean;
  search_term?: string;
  created_by_id?: string;
  skip?: number;
  limit?: number;
}

export interface TextStatistics {
  total_texts: number;
  texts_by_type: Record<string, number>;
  texts_by_language: Record<string, number>;
  texts_with_linked_words: number;
  primary_texts: number;
}

