import api from './api';

export interface Document {
  id: string;
  content: string;
  document_type: string;
  language_id?: string;
  source?: string;
  notes?: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentListItem {
  id: string;
  content: string;
  document_type: string;
  language_id?: string;
  created_at: string;
}

export interface CreateDocumentData {
  content: string;
  document_type: string;
  language_id?: string;
  source?: string;
  notes?: string;
}

export const documentService = {
  async getAll(params?: {
    skip?: number;
    limit?: number;
    language_id?: string;
    document_type?: string;
  }): Promise<DocumentListItem[]> {
    const response = await api.get<DocumentListItem[]>('/api/v1/documents/', { params });
    return response.data;
  },

  async getById(id: string): Promise<Document> {
    const response = await api.get<Document>(`/api/v1/documents/${id}`);
    return response.data;
  },

  async create(data: CreateDocumentData): Promise<Document> {
    const response = await api.post<Document>('/api/v1/documents/', data);
    return response.data;
  },

  async update(id: string, data: Partial<CreateDocumentData>): Promise<Document> {
    const response = await api.put<Document>(`/api/v1/documents/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/documents/${id}`);
  },
};

export default documentService;

