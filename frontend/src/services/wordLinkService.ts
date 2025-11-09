import api from './api';
import {
  TextWordLink,
  TextWordLinkCreate,
  TextWordLinkUpdate,
} from '../types/text';

export const wordLinkService = {
  async list(textId: string): Promise<TextWordLink[]> {
    const response = await api.get<TextWordLink[]>(`/api/v1/texts/${textId}/links`);
    return response.data;
  },

  async create(textId: string, data: TextWordLinkCreate): Promise<TextWordLink> {
    const response = await api.post<TextWordLink>(`/api/v1/texts/${textId}/links`, data);
    return response.data;
  },

  async update(textId: string, linkId: string, data: TextWordLinkUpdate): Promise<TextWordLink> {
    const response = await api.patch<TextWordLink>(`/api/v1/texts/${textId}/links/${linkId}`, data);
    return response.data;
  },

  async remove(textId: string, linkId: string): Promise<void> {
    await api.delete(`/api/v1/texts/${textId}/links/${linkId}`);
  },

  async regenerateSuggestions(textId: string): Promise<TextWordLink[]> {
    const response = await api.post<TextWordLink[]>(`/api/v1/texts/${textId}/links/suggest`);
    return response.data;
  },
};

export default wordLinkService;


