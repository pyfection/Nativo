import api from './api';
import { LexemeOrigin, LexemeRecommendation } from './wordService';

// -----------------------------------------------------------------------------
// Change proposals (matches backend/app/schemas/proposal.py)
// -----------------------------------------------------------------------------

export type ProposalStatus = 'open' | 'accepted' | 'rejected' | 'withdrawn';
export type VoteChoice = 'approve' | 'reject';

export interface ProposalVote {
  user_id: string;
  username?: string | null;
  choice: VoteChoice;
  comment?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LexemeUsage {
  lexeme_id: string;
  lemma: string;
  origin?: LexemeOrigin | null;
  recommendation: LexemeRecommendation;
  text_count: number;
  audio_count: number;
  locations: string[];
}

export interface ChangeProposal {
  id: string;
  language_id: string;
  lexeme_id?: string | null;
  lexeme_lemma?: string | null;
  proposal_type: 'set_recommendation' | 'add_spelling_variant' | 'add_translation';
  payload: { recommendation: LexemeRecommendation; note?: string | null };
  rationale?: string | null;
  status: ProposalStatus;
  created_by_id?: string | null;
  created_by_username?: string | null;
  created_at: string;
  resolved_at?: string | null;
  approvals: number;
  rejections: number;
  threshold: number;
  votes: ProposalVote[];
  usage: LexemeUsage[];
}

export interface RecommendationProposalCreate {
  recommendation: LexemeRecommendation;
  note?: string;
  rationale?: string;
}

const proposalService = {
  async listForWord(lexemeId: string): Promise<ChangeProposal[]> {
    const response = await api.get<ChangeProposal[]>(`/api/v1/words/${lexemeId}/proposals`);
    return response.data;
  },

  async listOpen(languageId: string): Promise<ChangeProposal[]> {
    const response = await api.get<ChangeProposal[]>('/api/v1/proposals', {
      params: { language_id: languageId, status_filter: 'open' },
    });
    return response.data;
  },

  async proposeRecommendation(
    lexemeId: string,
    data: RecommendationProposalCreate,
  ): Promise<ChangeProposal> {
    const response = await api.post<ChangeProposal>(
      `/api/v1/words/${lexemeId}/proposals/recommendation`,
      data,
    );
    return response.data;
  },

  async vote(proposalId: string, choice: VoteChoice, comment?: string): Promise<ChangeProposal> {
    const response = await api.post<ChangeProposal>(`/api/v1/proposals/${proposalId}/votes`, {
      choice,
      ...(comment && { comment }),
    });
    return response.data;
  },

  /** Settle a suggested addition (spelling variant, translation link). */
  async review(proposalId: string, approve: boolean): Promise<ChangeProposal> {
    const response = await api.post<ChangeProposal>(`/api/v1/proposals/${proposalId}/review`, {
      approve,
    });
    return response.data;
  },

  async withdraw(proposalId: string): Promise<ChangeProposal> {
    const response = await api.post<ChangeProposal>(`/api/v1/proposals/${proposalId}/withdraw`);
    return response.data;
  },
};

export default proposalService;
