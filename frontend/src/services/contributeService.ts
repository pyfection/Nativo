import api from './api';
import { ChangeProposal } from './proposalService';
import { TranslationLink } from './wordService';

/** Where a word was seen: an excerpt with the word's offsets in it. */
export interface TextContext {
  text_id: string;
  document_id: string | null;
  title: string;
  snippet: string;
  highlight_start: number;
  highlight_end: number;
}

interface TaskBase {
  /** Stable per-item id; sent back as `exclude` when the card is skipped. */
  key: string;
}

export interface DefineWordTask extends TaskBase {
  type: 'define_word';
  token: string;
  occurrences: number;
  context: TextContext;
}

export interface RecordAudioTask extends TaskBase {
  type: 'record_audio';
  lexeme_id: string;
  word_form_id: string;
  form: string;
  ipa_pronunciation: string | null;
  translations: TranslationLink[];
  uses: number;
}

export interface ConfirmLinkTask extends TaskBase {
  type: 'confirm_link';
  link_id: string;
  context: TextContext;
  lexeme_id: string;
  word_form_id: string;
  form: string;
  lemma: string;
  confidence: number | null;
  translations: TranslationLink[];
}

export interface ReviewWordTask extends TaskBase {
  type: 'review_word';
  lexeme_id: string;
  lemma: string;
  part_of_speech: string | null;
  ipa_pronunciation: string | null;
  notes: string | null;
  creator_username: string | null;
  translations: TranslationLink[];
}

export interface VoteTask extends TaskBase {
  type: 'vote';
  proposal: ChangeProposal;
}

export type ContributeTask =
  | DefineWordTask
  | RecordAudioTask
  | ConfirmLinkTask
  | ReviewWordTask
  | VoteTask;

export interface DefineWordAnswer {
  token?: string;
  lemma: string;
  part_of_speech?: string;
  gloss?: string;
  gloss_language_id?: string;
}

export interface DefineWordResult {
  lexeme_id: string;
  status: string;
}

const contributeService = {
  /** A varied deck of small tasks the user can do in this language. */
  async getTasks(languageId: string, exclude: string[], limit = 10): Promise<ContributeTask[]> {
    const response = await api.get<ContributeTask[]>(`/api/v1/contribute/${languageId}/tasks`, {
      params: { limit, exclude },
      // FastAPI reads repeated keys (exclude=a&exclude=b), not exclude[]=a.
      paramsSerializer: { indexes: null },
    });
    return response.data;
  },

  async defineWord(languageId: string, answer: DefineWordAnswer): Promise<DefineWordResult> {
    const response = await api.post<DefineWordResult>(
      `/api/v1/contribute/${languageId}/define`,
      answer,
    );
    return response.data;
  },
};

export default contributeService;
