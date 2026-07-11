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
  WRITING_STANDARD = 'writing_standard',

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

/** How a Text's content should be rendered. Plain prose vs. markdown. */
export enum TextFormat {
  PLAIN = 'plain',
  MARKDOWN = 'markdown',
}

/** Publication state: suggestions from non-editors start pending_review. */
export enum TextStatus {
  PENDING_REVIEW = 'pending_review',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

export interface TextWordLink {
  id: string;
  text_id: string;
  word_form_id: string;
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
  // Surface form (matching word_form_id)
  word_text?: string | null;
  word_form_romanization?: string | null;
  word_form_ipa?: string | null;
  word_form_notes?: string | null;
  // Parent lexeme (the dictionary entry)
  lexeme_id?: string | null;
  word_lemma?: string | null;
  word_part_of_speech?: string | null;
  word_notes?: string | null;
  word_language_id?: string | null;
}

export interface TextWordLinkCreate {
  word_form_id: string;
  start_char: number;
  end_char: number;
  status?: TextWordLinkStatus;
  notes?: string;
}

export interface TextWordLinkUpdate {
  status?: TextWordLinkStatus;
  notes?: string;
  word_form_id?: string;
}

export interface Text {
  id: string;
  title: string;
  content: string;
  document_type: DocumentType;
  format?: TextFormat;
  status?: TextStatus;
  language_id?: string;
  document_id?: string;
  is_primary: boolean;
  source?: string;
  notes?: string;
  /** Editor pin for the guided learning path (null = computed placement). */
  learning_order?: number | null;
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
  /** Confirmed-link coverage (0..1); populated by the document endpoints. */
  link_coverage?: number | null;
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
  format?: TextFormat;
  language_id?: string;
  document_id?: string;
  is_primary?: boolean;
  source?: string;
  notes?: string;
  learning_order?: number | null;
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
