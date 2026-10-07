"""
Nativo MCP server — the dictionary, spelling standard and texts as tools for
LLM clients (Claude Code, Claude Desktop, claude.ai connectors, ...).

Two transports, one tool set:
- Streamable HTTP at `/mcp`, mounted on the FastAPI app (`app.main`). The
  caller authenticates per request with `Authorization: Bearer <token>`.
- stdio via the `nativo-mcp` script, for local use against `DATABASE_URL`.
  The caller is whoever `NATIVO_API_TOKEN` belongs to.

Tools delegate to the REST endpoint functions rather than re-implementing
them, so permission checks and the suggester flow (writes by non-editors land
as pending suggestions) behave exactly as they do over REST. Read tools work
anonymously; write tools need a token — a personal API token (`nat_...`, from
POST /api/v1/auth/tokens) or a login JWT.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from fastapi import HTTPException
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from starlette.applications import Starlette

from app.api.deps import get_current_user
from app.api.v1.endpoints import contribute, documents, words
from app.database import SessionLocal
from app.models.language import Language
from app.models.text import Text
from app.models.user import User, UserRole
from app.models.user_language import UserLanguage
from app.schemas.contribute import SourceTextCreate
from app.schemas.document import DocumentListItem, DocumentWithTexts
from app.schemas.language import LanguageListItem
from app.schemas.text import Text as TextSchema
from app.schemas.text import TextCreate
from app.schemas.word import (
    AntonymCreate,
    AntonymLink,
    LexemeCreate,
    LexemeRejection,
    LexemeReviewCorrections,
    LexemeSuggestion,
    LexemeUpdate,
    LexemeWithForms,
    RhymeMatch,
    SpellingCorrection,
    SpellingResolution,
    SpellingVariantCreate,
    SynonymCreate,
    SynonymLink,
    TranslationCreate,
    TranslationLink,
    WordFormCreate,
    WordFormCreateNested,
    WordFormUpdate,
)
from app.schemas.word import Lexeme as LexemeSchema
from app.schemas.word import SpellingVariant as SpellingVariantSchema
from app.schemas.word import WordForm as WordFormSchema
from app.services import lexeme_service, spelling_service

INSTRUCTIONS = """\
Nativo preserves endangered languages: a dictionary, a written spelling
standard, and texts with translations.

- Everything is keyed by UUID. Start with `list_languages` to get language IDs.
- A *lexeme* ("word") is a dictionary entry; its *word forms* are the concrete
  written forms (one is the lemma), each with IPA. Translations, synonyms and
  antonyms link lexemes to each other, across or within languages.
- Before writing in a language, read its `get_writing_standard` and check
  spellings with `check_spelling` / `resolve_spelling`: the dictionary's word
  forms ARE the standard spelling.
- Writes need a Nativo API token. Editors of a language publish directly;
  anyone else's new words and texts land as suggestions pending review (check
  `status` in the result). `whoami` shows which languages you can edit.
"""

mcp = MCPServer(name="nativo", title="Nativo", instructions=INSTRUCTIONS)

# Overridable for tests; the HTTP and stdio transports both use the app's DB.
session_factory = SessionLocal

# Token for transports without HTTP headers (stdio), set by `main()`. Never
# consulted for HTTP requests — otherwise every remote caller would act as
# the server's own user.
_local_token: str | None = None

READ = ToolAnnotations(read_only_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)


@contextmanager
def _db() -> Iterator[Session]:
    """A session per tool call; endpoint HTTPExceptions become tool errors
    the model can read (404s, 403s, validation problems)."""
    db = session_factory()
    try:
        yield db
    except HTTPException as exc:
        db.rollback()
        raise ToolError(str(exc.detail)) from exc
    finally:
        db.close()


def _bearer_token(ctx: Context) -> str | None:
    headers = ctx.headers
    if headers is None:
        return _local_token
    scheme, _, token = (headers.get("authorization") or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


async def _user(ctx: Context, db: Session) -> User | None:
    """The calling user, or None when anonymous. A token that IS sent must
    be valid — a revoked token errors instead of silently going anonymous."""
    token = _bearer_token(ctx)
    if token is None:
        return None
    user = await get_current_user(token=token, db=db)
    if not user.is_active:
        raise ToolError("This Nativo account is inactive")
    return user


async def _require_user(ctx: Context, db: Session) -> User:
    user = await _user(ctx, db)
    if user is None:
        raise ToolError(
            "This tool needs a Nativo API token. Create one under Account → API "
            "tokens, then send it as `Authorization: Bearer <token>` (HTTP) or "
            "set NATIVO_API_TOKEN (stdio)."
        )
    return user


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


class LanguageAccess(BaseModel):
    language_id: UUID
    language_name: str
    proficiency: str
    can_edit: bool
    can_verify: bool


class WhoAmI(BaseModel):
    authenticated: bool
    user_id: UUID | None = None
    username: str | None = None
    is_admin: bool = False
    languages: list[LanguageAccess] = []


@mcp.tool(annotations=READ)
async def whoami(ctx: Context) -> WhoAmI:
    """Who the server sees you as, and which languages you may edit or review.
    Admins may edit and review every language."""
    with _db() as db:
        user = await _user(ctx, db)
        if user is None:
            return WhoAmI(authenticated=False)
        rows = (
            db.query(UserLanguage)
            .options(joinedload(UserLanguage.language))
            .filter(UserLanguage.user_id == user.id)
            .all()
        )
        return WhoAmI(
            authenticated=True,
            user_id=user.id,
            username=user.username,
            is_admin=bool(user.is_superuser or user.role == UserRole.ADMIN),
            languages=[
                LanguageAccess(
                    language_id=row.language_id,
                    language_name=row.language.name,
                    proficiency=row.proficiency_level.value,
                    can_edit=row.can_edit,
                    can_verify=row.can_verify,
                )
                for row in rows
            ],
        )


@mcp.tool(annotations=READ)
def list_languages(endangered: bool | None = None) -> list[LanguageListItem]:
    """List the languages in Nativo with their IDs. Optionally filter to
    endangered (true) or non-endangered (false) languages."""
    with _db() as db:
        query = db.query(Language)
        if endangered is not None:
            query = query.filter(Language.is_endangered == endangered)
        return [LanguageListItem.model_validate(lang) for lang in query.all()]


@mcp.tool(annotations=READ)
async def get_writing_standard(language_id: UUID, ctx: Context) -> DocumentWithTexts:
    """The written spelling standard (orthography rules) of a language, as a
    document. Read this before writing text in the language."""
    with _db() as db:
        language = db.query(Language).filter(Language.id == language_id).first()
        if language is None:
            raise ToolError("Language not found")
        if language.writing_standard_document_id is None:
            raise ToolError(f"{language.name} has no writing standard yet")
        return await documents.get_document(
            document_id=language.writing_standard_document_id,
            current_user=await _user(ctx, db),
            db=db,
        )


@mcp.tool(annotations=READ)
def search_words(
    query: str,
    language_id: UUID | None = None,
    include_unpublished: bool = False,
    limit: int = 20,
) -> list[LexemeWithForms]:
    """Search the dictionary by lemma, any written form, romanization, or a
    known non-standard spelling (which surfaces the standard entry it maps to).
    Matching is a case-insensitive substring match."""
    with _db() as db:
        lexemes = lexeme_service.search_lexemes(
            db,
            query,
            language_ids=[language_id] if language_id else None,
            include_unpublished=include_unpublished,
            limit=min(max(limit, 1), 100),
        )
        return [LexemeWithForms.model_validate(lx) for lx in lexemes]


class WordEntry(LexemeWithForms):
    translations: list[TranslationLink] = []
    synonyms: list[SynonymLink] = []
    antonyms: list[AntonymLink] = []


@mcp.tool(annotations=READ)
async def get_word(lexeme_id: UUID) -> WordEntry:
    """A full dictionary entry: the lexeme, all its word forms (with IPA),
    and its translations, synonyms and antonyms."""
    with _db() as db:
        lexeme = await words.get_lexeme(lexeme_id=lexeme_id, db=db)
        entry = WordEntry.model_validate(lexeme)
        entry.translations = lexeme_service.list_translations(db, lexeme_id)
        entry.synonyms = lexeme_service.list_synonyms(db, lexeme_id)
        entry.antonyms = lexeme_service.list_antonyms(db, lexeme_id)
        return entry


@mcp.tool(annotations=READ)
async def find_rhymes(word_form_id: UUID, near: bool = False, limit: int = 50) -> list[RhymeMatch]:
    """Word forms in the same language that rhyme with the given form, by IPA.
    `near=true` loosens the match to near rhymes."""
    with _db() as db:
        return await words.find_rhymes(
            form_id=word_form_id, near=near, limit=min(max(limit, 1), 200), db=db
        )


@mcp.tool(annotations=READ)
def resolve_spelling(language_id: UUID, word: str) -> SpellingResolution:
    """Check one written word against a language's standard spelling.
    `already_standard` is true when it is correct; otherwise `candidates`
    lists the standard forms it is a known variant of (possibly none)."""
    with _db() as db:
        return spelling_service.resolve_token(db, language_id, word)


@mcp.tool(annotations=READ)
def check_spelling(language_id: UUID, text: str) -> list[SpellingCorrection]:
    """Scan a passage for words written in a known non-standard way and
    propose the standard spelling for each (character offsets included).
    Words the dictionary doesn't know at all are not reported. Nothing is
    saved."""
    with _db() as db:
        # Transient Text — never added to the session, so nothing persists.
        passage = Text(language_id=language_id, content=text)
        return spelling_service.suggest_corrections_for_text(db, passage)


@mcp.tool(annotations=READ)
async def list_documents(
    ctx: Context,
    language_id: UUID | None = None,
    search: str | None = None,
    limit: int = 50,
) -> list[DocumentListItem]:
    """List documents (texts with their translations), optionally only those
    with a text in `language_id`, or whose title/content contains `search`."""
    with _db() as db:
        return await documents.list_documents(
            skip=0,
            limit=min(max(limit, 1), 200),
            language_id=language_id,
            search_term=search,
            current_user=await _user(ctx, db),
            db=db,
        )


@mcp.tool(annotations=READ)
async def get_document(document_id: UUID, ctx: Context) -> DocumentWithTexts:
    """A document with the full title and content of each of its texts
    (one per language)."""
    with _db() as db:
        return await documents.get_document(
            document_id=document_id, current_user=await _user(ctx, db), db=db
        )


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------


@mcp.tool(annotations=WRITE)
async def create_word(word: LexemeCreate, ctx: Context) -> LexemeWithForms:
    """Add a dictionary entry with its lemma form (and optionally more forms).
    Search first to avoid duplicates. If you can't edit the language, the entry
    is created as a suggestion (status `pending_review`) for a reviewer."""
    with _db() as db:
        user = await _require_user(ctx, db)
        lexeme = await words.create_lexeme(data=word, current_user=user, db=db)
        return LexemeWithForms.model_validate(lexeme)


@mcp.tool(annotations=WRITE)
async def update_word(lexeme_id: UUID, changes: LexemeUpdate, ctx: Context) -> LexemeSchema:
    """Change a dictionary entry's lexeme-level fields (part of speech, gender,
    notes, source, tags, ...). Only the fields you send change. Needs edit
    rights on the language."""
    with _db() as db:
        user = await _require_user(ctx, db)
        lexeme = await words.update_lexeme(
            lexeme_id=lexeme_id, data=changes, current_user=user, db=db
        )
        return LexemeSchema.model_validate(lexeme)


@mcp.tool(annotations=WRITE)
async def add_word_form(
    lexeme_id: UUID, form: WordFormCreateNested, ctx: Context
) -> WordFormSchema:
    """Add a written form (e.g. plural, a case form) to a dictionary entry.
    Include IPA when known — it drives rhyme search. Needs edit rights."""
    with _db() as db:
        user = await _require_user(ctx, db)
        data = WordFormCreate(**form.model_dump(), lexeme_id=lexeme_id)
        word_form = await words.add_form(lexeme_id=lexeme_id, data=data, current_user=user, db=db)
        return WordFormSchema.model_validate(word_form)


@mcp.tool(annotations=WRITE)
async def update_word_form(
    word_form_id: UUID, changes: WordFormUpdate, ctx: Context
) -> WordFormSchema:
    """Change a word form (spelling, IPA, inflection, notes). Only the fields
    you send change. Needs edit rights."""
    with _db() as db:
        user = await _require_user(ctx, db)
        word_form = await words.update_form(
            form_id=word_form_id, data=changes, current_user=user, db=db
        )
        return WordFormSchema.model_validate(word_form)


@mcp.tool(annotations=WRITE)
async def add_translation(
    lexeme_id: UUID, other_lexeme_id: UUID, ctx: Context, notes: str | None = None
) -> TranslationLink:
    """Link two dictionary entries in different languages as translations of
    each other. Both entries must exist (create the other one first)."""
    with _db() as db:
        user = await _require_user(ctx, db)
        return await words.add_translation(
            lexeme_id=lexeme_id,
            data=TranslationCreate(other_lexeme_id=other_lexeme_id, notes=notes),
            current_user=user,
            db=db,
        )


@mcp.tool(annotations=WRITE)
async def add_synonym(lexeme_id: UUID, synonym: SynonymCreate, ctx: Context) -> SynonymLink:
    """Mark two entries in the same language as synonyms, optionally with
    how they differ (`nuance`)."""
    with _db() as db:
        user = await _require_user(ctx, db)
        return await words.add_synonym(lexeme_id=lexeme_id, data=synonym, current_user=user, db=db)


@mcp.tool(annotations=WRITE)
async def add_antonym(lexeme_id: UUID, antonym: AntonymCreate, ctx: Context) -> AntonymLink:
    """Mark two entries in the same language as antonyms, optionally with the
    kind of opposition (`antonym_type`)."""
    with _db() as db:
        user = await _require_user(ctx, db)
        return await words.add_antonym(lexeme_id=lexeme_id, data=antonym, current_user=user, db=db)


@mcp.tool(annotations=WRITE)
async def add_spelling_variant(
    word_form_id: UUID, variant: str, ctx: Context, note: str | None = None
) -> SpellingVariantSchema:
    """Record a non-standard way a word form gets written, so spelling checks
    can map it back to the standard form. Needs edit rights."""
    with _db() as db:
        user = await _require_user(ctx, db)
        row = await words.add_spelling_variant(
            form_id=word_form_id,
            data=SpellingVariantCreate(variant=variant, note=note),
            current_user=user,
            db=db,
        )
        return SpellingVariantSchema.model_validate(row)


@mcp.tool(annotations=WRITE)
async def add_source_text(
    language_id: UUID,
    source_url: str,
    source_title: str,
    text: str,
    ctx: Context,
    license: str | None = None,
) -> int:
    """Store text from an outside page written in `language_id` (e.g. a
    Wikipedia article you fetched) as sentence snippets. Contributors then
    confirm the standard spelling of its unknown words, and people who speak
    the language translate its sentences. Pass the page URL, its title and
    licence (e.g. "CC BY-SA 4.0") so cards can credit it. Needs edit rights
    on the language. Returns how many new sentences were stored."""
    with _db() as db:
        user = await _require_user(ctx, db)
        result = contribute.add_source_text(
            language_id=language_id,
            data=SourceTextCreate(
                source_url=source_url, source_title=source_title, text=text, license=license
            ),
            current_user=user,
            db=db,
        )
        return result.created


@mcp.tool(annotations=WRITE)
async def create_document(text: TextCreate, ctx: Context) -> DocumentWithTexts:
    """Create a document with its first text. If you can't edit the text's
    language, it is created as a suggestion (status `pending_review`)."""
    with _db() as db:
        user = await _require_user(ctx, db)
        document = await documents.create_document(text_data=text, current_user=user, db=db)
        return DocumentWithTexts.model_validate(document)


@mcp.tool(annotations=WRITE)
async def add_document_text(document_id: UUID, text: TextCreate, ctx: Context) -> TextSchema:
    """Add a text in another language (a translation) to an existing
    document. Non-editors' texts land as suggestions pending review."""
    with _db() as db:
        user = await _require_user(ctx, db)
        row = await documents.add_translation(
            document_id=document_id, text_data=text, current_user=user, db=db
        )
        return TextSchema.model_validate(row)


# ---------------------------------------------------------------------------
# Review tools (need verify rights on the language)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ)
async def list_word_suggestions(language_id: UUID, ctx: Context) -> list[LexemeSuggestion]:
    """The review queue: suggested dictionary entries waiting for approval."""
    with _db() as db:
        user = await _require_user(ctx, db)
        return await words.list_suggestions(language_id=language_id, current_user=user, db=db)


@mcp.tool(annotations=WRITE)
async def approve_word(
    lexeme_id: UUID, ctx: Context, corrections: LexemeReviewCorrections | None = None
) -> LexemeSchema:
    """Approve a suggested (or any) dictionary entry: it becomes published
    and verified, together with the glosses drafted for it. Optional
    `corrections` (spelling, forms, part of speech, glosses) apply first."""
    with _db() as db:
        user = await _require_user(ctx, db)
        lexeme = await words.verify_lexeme(
            lexeme_id=lexeme_id, corrections=corrections, current_user=user, db=db
        )
        return LexemeSchema.model_validate(lexeme)


@mcp.tool(annotations=WRITE)
async def reject_word(lexeme_id: UUID, ctx: Context, reason: str | None = None) -> LexemeSchema:
    """Reject a pending suggestion. It is archived, with the reason kept in
    its notes."""
    with _db() as db:
        user = await _require_user(ctx, db)
        lexeme = await words.reject_lexeme(
            lexeme_id=lexeme_id,
            payload=LexemeRejection(reason=reason),
            current_user=user,
            db=db,
        )
        return LexemeSchema.model_validate(lexeme)


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


def http_app() -> Starlette:
    """Streamable HTTP app serving `/mcp`. Stateless with JSON responses, so
    any Fly machine can answer any request without session affinity. DNS
    rebinding protection is off: it guards unauthenticated localhost servers,
    and this one is public and authenticates writes by bearer token."""
    return mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


def main() -> None:
    """stdio entry point (`uv run nativo-mcp`)."""
    global _local_token
    _local_token = os.getenv("NATIVO_API_TOKEN") or None
    mcp.run("stdio")


if __name__ == "__main__":
    main()
