"""
AI suggestions for Quick Contribute word cards.

For a word seen in a published text (or an outside snippet) the AI suggests
its dictionary form, part of speech, meaning in the gloss language, and —
when the word as written breaks the language's writing standard — its
standard spelling. The prompt carries the sentence, the writing standard
document and a few reviewed dictionary entries as examples.

Suggest-only: the card pre-fills its fields and the person checks them;
their answer goes through the normal define / review flow. One suggestion is
made per (language, word, gloss language) and stored in `ai_suggestions`, so
every later user who gets the card sees it without another call.

Only words that occur in the given text/snippet of the language can be asked
about, which bounds what the endpoint can spend to the corpus.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.config import settings
from app.models.ai_suggestion import AiSuggestion
from app.models.language import Language
from app.models.source_snippet import SourceSnippet
from app.models.text import Text, TextStatus
from app.models.word import Lexeme, LexemeStatus, PartOfSpeech, lexeme_translations
from app.schemas.contribute import WordSuggestion
from app.utils import claude_cli
from app.utils.text_normalize import fold_for_match, iter_tokens

KIND_WORD = "word"

# Writing standards can be long; the rules that matter come first.
MAX_STANDARD_CHARS = 8000
MAX_EXAMPLES = 15
CONTEXT_RADIUS = 200

SYSTEM_PROMPT = (
    "You help volunteers build a dictionary of an endangered language. You get "
    "one word as it appears in a sentence and suggest its dictionary entry. A "
    "person checks every suggestion before it is saved. Follow the language's "
    "writing standard when one is given. Use null for any field you are not "
    "reasonably sure about rather than guessing."
)

_POS = [pos.value for pos in PartOfSpeech]

SCHEMA = {
    "type": "object",
    "properties": {
        "lemma": {"type": ["string", "null"]},
        "part_of_speech": {"type": ["string", "null"], "enum": [*_POS, None]},
        "gloss": {"type": ["string", "null"]},
        "standard_spelling": {"type": ["string", "null"]},
        "explanation": {"type": ["string", "null"]},
    },
    "required": ["lemma", "part_of_speech", "gloss", "standard_spelling", "explanation"],
    "additionalProperties": False,
}


def _occurrence(content: str, folded: str) -> tuple[int, int] | None:
    for token, start, end in iter_tokens(content or ""):
        if fold_for_match(token) == folded:
            return start, end
    return None


def _sentence(
    db: Session, language_id: UUID, folded: str, text_id: UUID | None, snippet_id: UUID | None
) -> str:
    """The passage around the word, from a published text or an outside
    snippet of this language that actually contains it."""
    content = None
    if text_id is not None:
        text = db.get(Text, text_id)
        if text and text.language_id == language_id and text.status == TextStatus.PUBLISHED:
            content = text.content
    elif snippet_id is not None:
        snippet = db.get(SourceSnippet, snippet_id)
        if snippet and snippet.language_id == language_id:
            content = snippet.content
    span = _occurrence(content, folded) if content else None
    if span is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Word not found in that text"
        )
    start, end = span
    lo, hi = max(0, start - CONTEXT_RADIUS), min(len(content), end + CONTEXT_RADIUS)
    return ("…" if lo else "") + content[lo:hi].strip() + ("…" if hi < len(content) else "")


def _writing_standard(db: Session, language: Language) -> str | None:
    if language.writing_standard_document_id is None:
        return None
    texts = (
        db.query(Text)
        .filter(Text.document_id == language.writing_standard_document_id)
        .order_by(Text.created_at.asc())
        .all()
    )
    text = next((t for t in texts if t.language_id == language.id), texts[0] if texts else None)
    if text is None or not text.content:
        return None
    return text.content[:MAX_STANDARD_CHARS]


def _examples(db: Session, language_id: UUID, gloss_language_id: UUID | None) -> list[str]:
    """Reviewed entries with a part of speech (and a meaning in the gloss
    language), newest first, as "lemma — pos — meaning" lines."""
    query = db.query(Lexeme).filter(
        Lexeme.language_id == language_id,
        Lexeme.status == LexemeStatus.PUBLISHED,
        Lexeme.part_of_speech.isnot(None),
    )
    if gloss_language_id is None:
        return [
            f"{lx.lemma} — {lx.part_of_speech.value}"
            for lx in query.order_by(Lexeme.created_at.desc()).limit(MAX_EXAMPLES)
        ]

    gloss = aliased(Lexeme)
    rows = (
        query.join(
            lexeme_translations,
            or_(
                lexeme_translations.c.lexeme_id == Lexeme.id,
                lexeme_translations.c.translation_id == Lexeme.id,
            ),
        )
        .join(
            gloss,
            and_(
                or_(
                    gloss.id == lexeme_translations.c.lexeme_id,
                    gloss.id == lexeme_translations.c.translation_id,
                ),
                gloss.id != Lexeme.id,
                gloss.language_id == gloss_language_id,
            ),
        )
        .with_entities(Lexeme.id, Lexeme.lemma, Lexeme.part_of_speech, gloss.lemma)
        .order_by(Lexeme.created_at.desc())
        .limit(MAX_EXAMPLES * 4)
        .all()
    )
    meanings: dict[UUID, tuple[str, str, list[str]]] = {}
    for lexeme_id, lemma, pos, meaning in rows:
        entry = meanings.setdefault(lexeme_id, (lemma, pos.value, []))
        entry[2].append(meaning)
    return [
        f"{lemma} — {pos} — {', '.join(glosses)}"
        for lemma, pos, glosses in list(meanings.values())[:MAX_EXAMPLES]
    ]


def _prompt(
    language: Language,
    gloss_language: Language | None,
    token: str,
    sentence: str,
    standard: str | None,
    examples: list[str],
) -> str:
    name = language.name
    parts = [
        f"Language: {name}",
        f'Word as written in the text: "{token}"',
        f"Passage: {sentence}",
    ]
    if standard:
        parts.append(f"Writing standard of {name} (its spelling rules):\n<<<\n{standard}\n>>>")
    if examples:
        parts.append(
            f"Entries already in the {name} dictionary, for style:\n"
            + "\n".join(f"- {line}" for line in examples)
        )
    meaning = (
        f"- gloss: its meaning in {gloss_language.name} as used in the passage, in "
        f'dictionary form ("give", not "gives it"). Several meanings: comma-separated. '
        "Keep it short."
        if gloss_language
        else "- gloss: null."
    )
    explained_in = gloss_language.name if gloss_language else "English"
    parts.append(
        "Suggest:\n"
        f"- lemma: the dictionary (citation) form of the word in standard {name} spelling "
        "(e.g. the infinitive of a verb, the singular of a noun). If the word is a "
        "contraction, the dictionary form of its main word.\n"
        f"- part_of_speech: of the word as used here, one of: {', '.join(_POS)}.\n"
        f"{meaning}\n"
        "- standard_spelling: if the word as written breaks the writing standard (e.g. "
        "an outdated or non-standard spelling), the same word form written correctly; "
        "otherwise null.\n"
        f"- explanation: one short sentence in {explained_in} for the volunteer, e.g. "
        "what the form is made of."
    )
    return "\n\n".join(parts)


def _clean(raw: dict, token: str, with_gloss: bool) -> WordSuggestion:
    def text(key: str, limit: int = 255) -> str | None:
        value = raw.get(key)
        if not isinstance(value, str):
            return None
        value = " ".join(value.split())
        return value[:limit] or None

    try:
        pos = PartOfSpeech(raw.get("part_of_speech"))
    except ValueError:
        pos = None
    standard = text("standard_spelling")
    if standard and (" " in standard or fold_for_match(standard) == fold_for_match(token)):
        standard = None
    return WordSuggestion(
        lemma=text("lemma"),
        part_of_speech=pos,
        gloss=text("gloss") if with_gloss else None,
        standard_spelling=standard,
        explanation=text("explanation", 500),
    )


def suggest_word(
    db: Session,
    language_id: UUID,
    token: str,
    *,
    text_id: UUID | None = None,
    snippet_id: UUID | None = None,
    gloss_language_id: UUID | None = None,
) -> WordSuggestion:
    language = db.get(Language, language_id)
    if language is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    gloss_language = None
    if gloss_language_id is not None:
        if gloss_language_id == language_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A meaning needs another language to be written in",
            )
        gloss_language = db.get(Language, gloss_language_id)
        if gloss_language is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Meaning language not found"
            )

    token = token.strip()
    folded = fold_for_match(token)
    sentence = _sentence(db, language_id, folded, text_id, snippet_id)

    cached = (
        db.query(AiSuggestion)
        .filter(
            AiSuggestion.language_id == language_id,
            AiSuggestion.kind == KIND_WORD,
            AiSuggestion.key == folded,
            AiSuggestion.gloss_language_id == gloss_language_id
            if gloss_language_id
            else AiSuggestion.gloss_language_id.is_(None),
        )
        .first()
    )
    if cached is not None:
        return WordSuggestion.model_validate(cached.payload)

    prompt = _prompt(
        language,
        gloss_language,
        token,
        sentence,
        _writing_standard(db, language),
        _examples(db, language_id, gloss_language_id),
    )
    try:
        raw = claude_cli.ask_json(prompt, system=SYSTEM_PROMPT, schema=SCHEMA)
    except claude_cli.ClaudeUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    suggestion = _clean(raw, token, with_gloss=gloss_language is not None)

    db.add(
        AiSuggestion(
            language_id=language_id,
            kind=KIND_WORD,
            key=folded,
            gloss_language_id=gloss_language_id,
            payload=suggestion.model_dump(mode="json"),
            model=settings.AI_SUGGEST_MODEL,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # another request stored the same card first
    return suggestion
