import api from './api';
import type { OutboxConfig } from './outbox';
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

/** Where a word was seen outside Nativo: excerpt, link and licence. */
export interface SourceContext {
  snippet_id: string;
  snippet: string;
  highlight_start: number;
  highlight_end: number;
  source_url: string;
  source_title: string;
  license: string | null;
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

export interface ConfirmSpellingTask extends TaskBase {
  type: 'confirm_spelling';
  token: string;
  occurrences: number;
  source: SourceContext;
}

export interface TranslateWordTask extends TaskBase {
  type: 'translate_word';
  source_lexeme_id: string;
  lemma: string;
  source_language_id: string;
  part_of_speech: string | null;
  translations: TranslationLink[];
}

export interface TranslateTextTask extends TaskBase {
  type: 'translate_text';
  source_language_id: string;
  title: string;
  content: string;
  /** Internal text… */
  text_id: string | null;
  document_id: string | null;
  /** …or an outside snippet. */
  snippet_id: string | null;
  source_url: string | null;
  license: string | null;
}

export interface ReviewAdditionTask extends TaskBase {
  type: 'review_addition';
  proposal_id: string;
  proposal_type: 'add_spelling_variant' | 'add_translation';
  lexeme_id: string;
  lemma: string;
  variant: string | null;
  note: string | null;
  other_lemma: string | null;
  other_language_id: string | null;
  /** Accepting also corrects the old spelling in the language's texts. */
  fix_texts: boolean;
  creator_username: string | null;
}

export type ContributeTask =
  | DefineWordTask
  | RecordAudioTask
  | ConfirmLinkTask
  | ReviewWordTask
  | VoteTask
  | ConfirmSpellingTask
  | TranslateWordTask
  | TranslateTextTask
  | ReviewAdditionTask;

export interface DefineWordAnswer {
  token?: string;
  /** The standard spelling of `token` when the text misspells it. */
  corrected?: string;
  lemma: string;
  part_of_speech?: string;
  gloss?: string;
  gloss_language_id?: string;
}

export interface DefineWordResult {
  lexeme_id: string;
  status: string;
  outcome: ContributeResult['outcome'];
}

/** AI suggestion for a word card; null fields mean the AI wasn't sure. */
export interface WordSuggestion {
  lemma: string | null;
  part_of_speech: string | null;
  gloss: string | null;
  /** How the word should be written, when the text breaks the standard. */
  standard_spelling: string | null;
  explanation: string | null;
}

export interface WordSuggestionQuery {
  token: string;
  text_id?: string;
  snippet_id?: string;
  gloss_language_id?: string;
}

export interface SpellingAnswer {
  token: string;
  standard: string;
  snippet_id?: string;
  part_of_speech?: string;
  gloss?: string;
  gloss_language_id?: string;
}

export interface TranslateWordAnswer {
  source_lexeme_id: string;
  lemma: string;
  part_of_speech?: string;
}

export interface TranslateTextAnswer {
  text_id?: string;
  snippet_id?: string;
  title?: string;
  content: string;
}

/** published: live now · suggested: new entry awaiting review ·
 *  proposed: addition to an existing entry awaiting a reviewer. */
export interface ContributeResult {
  outcome: 'published' | 'suggested' | 'proposed';
  lexeme_id: string | null;
  document_id: string | null;
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

  /** AI suggestion for a word card. Rejects (503) when AI isn't set up. */
  async suggestWord(languageId: string, query: WordSuggestionQuery): Promise<WordSuggestion> {
    const response = await api.get<WordSuggestion>(`/api/v1/contribute/${languageId}/suggest`, {
      params: query,
    });
    return response.data;
  },

  async confirmSpelling(
    languageId: string,
    answer: SpellingAnswer,
    config?: OutboxConfig,
  ): Promise<ContributeResult> {
    const response = await api.post<ContributeResult>(
      `/api/v1/contribute/${languageId}/spelling`,
      answer,
      config,
    );
    return response.data;
  },

  async translateWord(
    languageId: string,
    answer: TranslateWordAnswer,
    config?: OutboxConfig,
  ): Promise<ContributeResult> {
    const response = await api.post<ContributeResult>(
      `/api/v1/contribute/${languageId}/translate-word`,
      answer,
      config,
    );
    return response.data;
  },

  async translateText(
    languageId: string,
    answer: TranslateTextAnswer,
    config?: OutboxConfig,
  ): Promise<ContributeResult> {
    const response = await api.post<ContributeResult>(
      `/api/v1/contribute/${languageId}/translate-text`,
      answer,
      config,
    );
    return response.data;
  },

  async defineWord(
    languageId: string,
    answer: DefineWordAnswer,
    config?: OutboxConfig,
  ): Promise<DefineWordResult> {
    const response = await api.post<DefineWordResult>(
      `/api/v1/contribute/${languageId}/define`,
      answer,
      config,
    );
    return response.data;
  },
};

export default contributeService;
