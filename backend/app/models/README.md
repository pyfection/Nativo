# Nativo Database Models

## Overview

All models use **UUID** primary keys for better distributed system compatibility and security.

---

## Core Models

### User
Authentication and contributor tracking.

**Key Fields:**
- `id` (UUID)
- `email`, `username` (unique)
- `hashed_password`
- `is_active`, `is_superuser`

**Relationships:**
- `words_created` - Words created by this user
- `words_verified` - Words verified by this user

---

### Language
Endangered languages being preserved.

**Key Fields:**
- `id` (UUID)
- `name`, `native_name`
- `iso_639_3` - ISO 639-3 language code
- `is_endangered`

**Relationships:**
- `words` - Words in this language
- `documents` - Documents in this language

---

### Document ⭐
**Unified model for ALL text content** - from full documents to small snippets.

**No title field!** Each document is typed by `document_type` enum instead.

**Key Fields:**
- `id` (UUID)
- `content` - The text content (can be short or long)
- `document_type` - Type enum (story, definition, etymology, etc.)
- `language_id` (FK → Language, optional) - Language of the content
- `source` - Where this content came from
- `notes` - Internal notes
- `created_by_id` (FK → User)

**Document Types (Enum):**

*Full documents:*
- `story`, `historical_record`, `book`, `article`, `transcription`

*Text snippets:*
- `definition`, `literal_translation`, `context_note`, `usage_example`
- `etymology`, `cultural_significance`, `translation`, `note`

*Other:*
- `other`

**Relationships:**
- `language` - Language of the content
- `linked_words` - Words that appear in this document's content (many-to-many)

**Use Cases:**
```python
# Full document
Document(
    content="Long story about creation...",
    document_type=DocumentType.STORY,
    language_id=indigenous_lang_id
)

# Definition snippet
Document(
    content="good health, spiritual and physical wellness",
    document_type=DocumentType.DEFINITION,
    language_id=english_id,  # English definition
    source="Historical Dictionary, 1890"
)

# Etymology snippet
Document(
    content="From wəli (good) + pemk (body) + anni (state)",
    document_type=DocumentType.ETYMOLOGY,
    source="Linguistic Research 2020"
)
```

**Word Linking Feature:**
Words in a document's content can be linked to actual Word records via `word_documents` many-to-many table. This enables:
- Annotating which words in a text correspond to dictionary entries
- Building connections between documents and vocabulary
- Tracking word usage across texts

---

### Location
Geographic location for tracking where words/pronunciations were confirmed.

**Key Fields:**
- `id` (UUID)
- `latitude`, `longitude` (required)
- `name` - Descriptive name (e.g., "Village of X")
- `description` - Additional context

**Use Cases:**
- Track dialectal variations by region
- Document where specific pronunciations were recorded
- Preserve geographic context of endangered languages

---

### Audio
Audio recordings for pronunciation.

**Key Fields:**
- `id` (UUID)
- `file_path`
- `file_size`, `duration`, `mime_type`
- `uploaded_by_id` (FK → User)

**Relationships:**
- Multiple words can reference the same audio file (many-to-many)

---

### Image
Visual references for words.

**Key Fields:**
- `id` (UUID)
- `file_path`, `alt_text`, `caption`
- `uploaded_by_id` (FK → User)

**Relationships:**
- Multiple words can reference the same image (many-to-many)

---

### Tag
Categorization tags for words (e.g., 'nature', 'family', 'ceremonial').

**Key Fields:**
- `id` (UUID)
- `name` (unique)
- `description`

**Relationships:**
- `words` - Words with this tag (many-to-many)

---

### Word ⭐
**Core vocabulary model** for endangered language preservation.

**Key Fields:**

*Core Information:*
- `id` (UUID)
- `word` - The word in the target language
- `language_id` (FK → Language)
- `romanization` - For non-Latin scripts
- `ipa_pronunciation` - IPA transcription

*Linguistic Information (all enums):*
- `part_of_speech` - Enum: noun, verb, adjective, etc.
- `gender` - Enum: masculine, feminine, neuter, animate, etc.
- `plurality` - Enum: singular, plural, dual, trial, etc.
- `grammatical_case` - Enum: nominative, accusative, genitive, etc.
- `verb_aspect` - Enum: perfective, imperfective, progressive, etc.
- `animacy` - Enum: animate, inanimate, human, etc.

*Cultural Context:*
- `register` - Enum: formal, informal, ceremonial, archaic, etc.

*Location:*
- `confirmed_at_id` (FK → Location) - Where this word/pronunciation was confirmed

*Metadata:*
- `created_by_id`, `verified_by_id`, `is_verified`, `status`, `source`, `notes`

**Relationships:**
- `language` - The language this word belongs to
- `confirmed_at` - Geographic location where confirmed
- `audio_files` - Multiple audio pronunciations (many-to-many)
- `images` - Multiple visual references (many-to-many)
- `tags` - Categorization tags (many-to-many)
- `documents` - Documents where this word is mentioned/defined (many-to-many)
- `synonyms`, `antonyms`, `related_words` - Self-referential relationships to other words

---

## Word Package Structure

The `word` module is organized as a **package** for better code organization:

```
app/models/word/
  __init__.py           # Exports all word-related items
  enums.py              # All linguistic enums
  word.py               # Word and Image models
  associations.py       # Association tables for many-to-many
```

### Enums (in `word/enums.py`)

#### PartOfSpeech (14 values)
`noun`, `verb`, `adjective`, `adverb`, `pronoun`, `preposition`, `conjunction`, `interjection`, `article`, `determiner`, `particle`, `numeral`, `classifier`, `other`

#### GrammaticalGender (7 values)
`masculine`, `feminine`, `neuter`, `common`, `animate`, `inanimate`, `not_applicable`

#### Plurality (7 values)
`singular`, `plural`, `dual`, `trial`, `paucal`, `collective`, `not_applicable`

#### GrammaticalCase (16 values)
**Core cases:**
- `nominative`, `accusative`, `genitive`, `dative`

**Additional common:**
- `ablative`, `locative`, `instrumental`, `vocative`

**Other cases:**
- `partitive`, `comitative`, `essive`, `translative`, `ergative`, `absolutive`
- `not_applicable`, `other`

#### VerbAspect (11 values)
`perfective`, `imperfective`, `progressive`, `continuous`, `habitual`, `iterative`, `inchoative`, `perfect`, `prospective`, `not_applicable`, `other`

#### Animacy (7 values)
`animate`, `inanimate`, `human`, `non_human`, `personal`, `impersonal`, `not_applicable`

#### Register (10 values)
`formal`, `informal`, `colloquial`, `slang`, `ceremonial`, `archaic`, `taboo`, `poetic`, `technical`, `neutral`

#### WordStatus (5 values)
`draft`, `pending_review`, `published`, `deprecated`, `archived`

---

## Association Tables

### word_tags
Word ↔ Tag (many-to-many)
- `word_id`, `tag_id`, `created_at`

### word_audio
Word ↔ Audio (many-to-many)
- `word_id`, `audio_id`, `is_primary`, `created_at`

### word_image
Word ↔ Image (many-to-many)
- `word_id`, `image_id`, `is_primary`, `created_at`

### word_documents ⭐
Word ↔ Document (many-to-many)
- `word_id`, `document_id`, `created_at`
- Links words to documents where they're mentioned or defined
- Enables word-linking feature in document content

### word_synonyms
Word ↔ Word (self-referential)
- `word_id`, `synonym_id`, `created_at`

### word_antonyms
Word ↔ Word (self-referential)
- `word_id`, `antonym_id`, `created_at`

### word_related
Word ↔ Word (self-referential with type)
- `word_id`, `related_word_id`, `relationship_type`, `created_at`
- `relationship_type` examples: 'derived_from', 'compound_part', 'root_of', etc.

---

## Database Indexes

**Indexed fields for performance:**
- `Word.word`, `Word.language_id`, `Word.romanization`
- `Word.part_of_speech`, `Word.is_verified`, `Word.status`
- `Document.document_type`, `Document.language_id`
- `Language.name`, `Language.iso_639_3`
- `User.email`, `User.username`
- `Tag.name`

---

## Example Usage

### Creating a Word with Multiple Documents

```python
from app.models import Word, Document, Location
from app.models.word import PartOfSpeech, GrammaticalGender, WordStatus
from app.models.document import DocumentType

# Create location
location = Location(
    latitude=45.5231,
    longitude=-122.6765,
    name="Portland, Oregon"
)

# Create the word
word = Word(
    word="wəlapəmkanni",
    language_id=indigenous_lang_id,
    romanization="welapemkanni",
    ipa_pronunciation="/wəlapəmkanni/",
    part_of_speech=PartOfSpeech.NOUN,
    gender=GrammaticalGender.ANIMATE,
    confirmed_at=location,
    created_by_id=user_id,
    status=WordStatus.PUBLISHED
)

# Create definition document
definition = Document(
    content="good health, spiritual and physical wellness",
    document_type=DocumentType.DEFINITION,
    language_id=english_id,  # English definition
    source="Elder Interview, March 2024",
    created_by_id=user_id
)

# Create etymology document
etymology = Document(
    content="From wəli (good) + pemk (body) + anni (state)",
    document_type=DocumentType.ETYMOLOGY,
    source="Linguistic Research, 2020",
    created_by_id=user_id
)

# Create cultural significance document
cultural = Document(
    content="Traditional greeting expressing wish for holistic wellness",
    document_type=DocumentType.CULTURAL_SIGNIFICANCE,
    source="Oral History Collection",
    created_by_id=user_id
)

# Link documents to word
word.documents.extend([definition, etymology, cultural])

# Add audio and tags
word.audio_files.append(native_speaker_audio)
word.tags.extend([health_tag, traditional_tag])

session.add_all([location, word, definition, etymology, cultural])
session.commit()
```

### Querying Words with Documents

```python
# Get word with all related documents
word = (
    session.query(Word)
    .options(
        joinedload(Word.documents),
        joinedload(Word.confirmed_at),
        joinedload(Word.audio_files),
        joinedload(Word.tags)
    )
    .filter(Word.id == word_id)
    .first()
)

# Access different types of documents
for doc in word.documents:
    if doc.document_type == DocumentType.DEFINITION:
        print(f"Definition: {doc.content}")
    elif doc.document_type == DocumentType.ETYMOLOGY:
        print(f"Etymology: {doc.content}")
    elif doc.document_type == DocumentType.CULTURAL_SIGNIFICANCE:
        print(f"Cultural: {doc.content}")
```

### Word-Linking in Documents

```python
# Create a story document
story = Document(
    content="The elder spoke of wəlapəmkanni and its importance...",
    document_type=DocumentType.STORY,
    language_id=indigenous_lang_id,
    created_by_id=user_id
)

# Link words mentioned in the story
word1 = session.query(Word).filter(Word.word == "wəlapəmkanni").first()
word2 = session.query(Word).filter(Word.word == "elder").first()

story.linked_words.extend([word1, word2])

session.add(story)
session.commit()

# Later: find all documents mentioning a word
documents_with_word = word1.documents
# Returns all documents where this word is linked
```

---

## Design Rationale

### Why Unified Document Model?

**Previous approach:** Separate `Document` (with title) and `Text` (without title) models

**Problem:** Unnecessary duplication - both models had almost identical fields

**Solution:** Single `Document` model typed by `document_type` enum

**Benefits:**
- ✅ Simpler schema - one model instead of two
- ✅ No confusion about when to use which
- ✅ Type-safe via enum (can't typo document types)
- ✅ Easy to query all content or filter by type
- ✅ Same document can serve multiple purposes

### Word-Linking Feature

The `word_documents` many-to-many relationship enables:
- Annotating texts with vocabulary links
- Finding all documents that mention a word
- Finding all words mentioned in a document
- Building a network of word usage across texts
- Enabling interactive reading with word definitions

**Future Enhancement:** Could add a `position` field to track where in the document the word appears, enabling precise highlighting.

---

## Migration Notes

When creating Alembic migrations:

1. **Create tables in this order** (respecting foreign key dependencies):
   - `users`
   - `languages`
   - `locations`
   - `audio`
   - `images`
   - `documents` (unified model, no title field)
   - `tags`
   - `words`
   - Association tables

2. **Ensure all enums are created** before tables that use them
   - `PartOfSpeech`, `GrammaticalGender`, `Plurality`, `GrammaticalCase`, `VerbAspect`, `Animacy`, `Register`, `WordStatus`
   - `DocumentType`

3. **All UUIDs** should use `UUID(as_uuid=True)` for PostgreSQL

Example migration:
```bash
alembic revision --autogenerate -m "Unified Document model with word-linking"
alembic upgrade head
```

---

## Future Enhancements

Potential additions:
1. **Position tracking** - Track exact position of linked words in document content
2. **Annotations** - Allow users to add notes/highlights to specific parts of documents
3. **Morphology** table for detailed inflection patterns
4. **Pronunciation Variants** - track different regional pronunciations with locations
5. **Historical Forms** table tracking language evolution over time
6. **Cognates** - linking to words in related languages
7. **Document versions** - Track edits to documents over time
