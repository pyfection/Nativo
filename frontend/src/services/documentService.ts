import api from './api';
import {
  Document,
  DocumentWithTexts,
  DocumentWithLinks,
  DocumentListItem,
  DocumentFilter,
} from '../types/document';
import { Text, TextCreate, TextStatus, TextUpdate } from '../types/text';

export type CreateDocumentData = TextCreate;

/** A pending text suggestion as shown in the reviewer's queue. */
export interface TextSuggestion {
  id: string;
  document_id?: string | null;
  title: string;
  content: string;
  document_type: string;
  language_id?: string | null;
  status: TextStatus;
  notes?: string | null;
  created_at: string;
  creator_username?: string | null;
}

/**
 * Document service for managing documents and their texts (translations).
 *
 * Documents group together Text records in multiple languages.
 * The service fetches documents and returns the text in the selected language.
 */
const documentService = {
  /**
   * Get all documents with filtering.
   * Returns documents with the text in the selected language (or primary if not available).
   */
  async getAll(params?: DocumentFilter & { language_id?: string }): Promise<DocumentListItem[]> {
    const response = await api.get<DocumentListItem[]>('/api/v1/documents/', { params });
    return response.data;
  },

  /**
   * Get a document by ID with all its texts.
   */
  async getById(id: string): Promise<DocumentWithTexts> {
    const response = await api.get<DocumentWithTexts>(`/api/v1/documents/${id}`);
    return response.data;
  },

  /**
   * Get a document by ID including link metadata.
   */
  async getWithLinks(id: string): Promise<DocumentWithLinks> {
    const response = await api.get<DocumentWithLinks>(`/api/v1/documents/${id}/links`);
    return response.data;
  },

  /**
   * Get a document's text in a specific language.
   * Returns the primary text if the requested language is not available.
   */
  async getByIdForLanguage(id: string, languageId: string): Promise<{ document: Document; text: Text }> {
    const response = await api.get<{ document: Document; text: Text }>(
      `/api/v1/documents/${id}/language/${languageId}`
    );
    return response.data;
  },

  /**
   * Create a new document with an initial text.
   */
  async create(data: CreateDocumentData): Promise<DocumentWithTexts> {
    const response = await api.post<DocumentWithTexts>('/api/v1/documents/', data);
    return response.data;
  },

  /**
   * Add a translation (new text) to an existing document.
   */
  async addTranslation(documentId: string, data: TextCreate): Promise<Text> {
    const response = await api.post<Text>(`/api/v1/documents/${documentId}/texts`, data);
    return response.data;
  },

  /**
   * Update a specific text within a document.
   */
  async updateText(documentId: string, textId: string, data: TextUpdate): Promise<Text> {
    const response = await api.put<Text>(`/api/v1/documents/${documentId}/texts/${textId}`, data);
    return response.data;
  },

  /**
   * Delete a document and all its texts.
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/documents/${id}`);
  },

  /**
   * Delete a specific text (translation) from a document.
   */
  async deleteText(documentId: string, textId: string): Promise<void> {
    await api.delete(`/api/v1/documents/${documentId}/texts/${textId}`);
  },

  /**
   * List pending text suggestions for a language (reviewers only).
   */
  async listSuggestions(languageId: string): Promise<TextSuggestion[]> {
    const response = await api.get<TextSuggestion[]>('/api/v1/documents/suggestions', {
      params: { language_id: languageId },
    });
    return response.data;
  },

  /**
   * Approve a pending text suggestion — it becomes published.
   */
  async approveText(documentId: string, textId: string): Promise<Text> {
    const response = await api.post<Text>(
      `/api/v1/documents/${documentId}/texts/${textId}/approve`
    );
    return response.data;
  },

  /**
   * Reject a pending text suggestion with an optional reason.
   */
  async rejectText(documentId: string, textId: string, reason?: string): Promise<Text> {
    const response = await api.post<Text>(
      `/api/v1/documents/${documentId}/texts/${textId}/reject`,
      reason ? { reason } : {}
    );
    return response.data;
  },

  /**
   * Regenerate auto-link suggestions for every text in a document.
   */
  async regenerateLinkSuggestions(documentId: string): Promise<DocumentWithLinks> {
    const response = await api.post<DocumentWithLinks>(`/api/v1/documents/${documentId}/links/suggest`);
    return response.data;
  },
};

export default documentService;
export { documentService };

