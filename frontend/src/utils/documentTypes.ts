import { DocumentType } from '../types/text';

export const DOCUMENT_TYPE_OPTIONS: Array<{ value: DocumentType; label: string }> = [
  { value: DocumentType.STORY, label: 'Story' },
  { value: DocumentType.HISTORICAL_RECORD, label: 'Historical Record' },
  { value: DocumentType.BOOK, label: 'Book' },
  { value: DocumentType.ARTICLE, label: 'Article' },
  { value: DocumentType.TRANSCRIPTION, label: 'Transcription' },
  { value: DocumentType.DEFINITION, label: 'Definition' },
  { value: DocumentType.LITERAL_TRANSLATION, label: 'Literal Translation' },
  { value: DocumentType.CONTEXT_NOTE, label: 'Context Note' },
  { value: DocumentType.USAGE_EXAMPLE, label: 'Usage Example' },
  { value: DocumentType.ETYMOLOGY, label: 'Etymology' },
  { value: DocumentType.CULTURAL_SIGNIFICANCE, label: 'Cultural Significance' },
  { value: DocumentType.TRANSLATION, label: 'Translation' },
  { value: DocumentType.NOTE, label: 'Note' },
  { value: DocumentType.OTHER, label: 'Other' },
];

export const documentTypeLabelMap: Record<DocumentType, string> = DOCUMENT_TYPE_OPTIONS.reduce(
  (acc, option) => {
    acc[option.value] = option.label;
    return acc;
  },
  {} as Record<DocumentType, string>
);

export function getDocumentTypeLabel(type: DocumentType | string | undefined): string {
  if (!type) return 'Unknown';

  const label =
    documentTypeLabelMap[type as DocumentType] ??
    type
      .toString()
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');

  return label;
}


