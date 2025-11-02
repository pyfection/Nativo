# Quick Start - Nativo Database Models

## TL;DR

**8 models. 1 Document model for all text. Word-linking feature. All UUIDs.**

---

## The Models

```
User          → Authentication
Language      → Endangered languages
Audio         → Pronunciation recordings
Document      → ALL text (no title field!)
Location      → GPS coordinates
Tag           → Categories
Image         → Pictures
Word          → Vocabulary (core model)
```

---

## Key Insight: Unified Document

**One model** handles:
- Full documents (stories, books)
- Small snippets (definitions, etymology)

**How?** Use `document_type` enum instead of title field.

```python
# Story
Document(
    content="Long creation story...",
    document_type=DocumentType.STORY
)

# Definition
Document(
    content="good health, wellness",
    document_type=DocumentType.DEFINITION
)
```

---

## Word-Linking Feature

Link words in documents to Word records:

```python
# Create story
story = Document(
    content="The elder spoke of wəlapəmkanni...",
    document_type=DocumentType.STORY
)

# Link word mentioned in story
word = Word(word="wəlapəmkanni")
story.linked_words.append(word)

# Find all documents mentioning this word
word.documents  # → [story, ...]
```

---

## Example: Complete Word Entry

```python
from app.models import Word, Document, Location, Audio, Tag
from app.models.word import PartOfSpeech, GrammaticalCase, WordStatus
from app.models.document import DocumentType

# 1. Create location
location = Location(
    latitude=45.52,
    longitude=-122.68,
    name="Portland, OR"
)

# 2. Create word
word = Word(
    word="wəlapəmkanni",
    romanization="welapemkanni",
    ipa_pronunciation="/wəlapəmkanni/",
    language_id=lang_id,
    part_of_speech=PartOfSpeech.NOUN,
    grammatical_case=GrammaticalCase.NOMINATIVE,
    confirmed_at=location,
    created_by_id=user_id,
    status=WordStatus.PUBLISHED
)

# 3. Create documents
definition = Document(
    content="good health, spiritual wellness",
    document_type=DocumentType.DEFINITION,
    source="Elder Interview 2024",
    created_by_id=user_id
)

etymology = Document(
    content="From wəli (good) + pemk (body) + anni (state)",
    document_type=DocumentType.ETYMOLOGY,
    source="Linguistic Research",
    created_by_id=user_id
)

# 4. Link everything
word.documents.extend([definition, etymology])
word.audio_files.append(audio)
word.tags.append(health_tag)

# 5. Save
session.add_all([location, word, definition, etymology])
session.commit()
```

---

## Document Types

**Full documents:**
- story, historical_record, book, article, transcription

**Snippets:**
- definition, etymology, literal_translation, context_note
- usage_example, cultural_significance, translation, note

**Other:**
- other

---

## Word Relationships (10 total)

1. `language` - Language (M:1)
2. `created_by` - User (M:1)
3. `verified_by` - User (M:1)
4. `confirmed_at` - Location (M:1)
5. `audio_files` - Audio (M:M)
6. `images` - Image (M:M)
7. `tags` - Tag (M:M)
8. **`documents`** - Document (M:M) ⭐ word-linking
9. `synonyms` - Word (M:M self-ref)
10. `antonyms` - Word (M:M self-ref)
11. `related_words` - Word (M:M self-ref)

---

## Querying

```python
# Get word with all related data
word = session.query(Word).options(
    joinedload(Word.documents),
    joinedload(Word.audio_files),
    joinedload(Word.tags),
    joinedload(Word.confirmed_at)
).filter(Word.id == word_id).first()

# Get all definitions
definitions = session.query(Document).filter(
    Document.document_type == DocumentType.DEFINITION
).all()

# Get all words confirmed in a region
words = session.query(Word).join(Location).filter(
    Location.latitude.between(45, 46),
    Location.longitude.between(-123, -122)
).all()

# Find words by tag
words = session.query(Word).join(Tag).filter(
    Tag.name == "ceremonial"
).all()
```

---

## File Structure

```
app/models/
  ├── user.py
  ├── language.py
  ├── audio.py
  ├── document.py      ← Unified (no title!)
  ├── location.py
  ├── tag.py
  └── word/            ← Package
      ├── enums.py     ← All linguistic enums
      ├── word.py      ← Word & Image models
      └── associations.py
```

---

## Next Steps

1. **Create migration:**
```bash
alembic revision --autogenerate -m "Create unified document model"
alembic upgrade head
```

2. **Import models:**
```python
from app.models import Word, Document, Location, Audio, Tag
from app.models.word import PartOfSpeech, GrammaticalCase, WordStatus
from app.models.document import DocumentType
```

3. **Start creating content!**

---

## Key Benefits

✅ **Simple** - One Document model, not two  
✅ **Flexible** - Any size content with type enum  
✅ **Word-linking** - Connect vocabulary to texts  
✅ **Type-safe** - Enums prevent typos  
✅ **Geographic** - Track where words were confirmed  
✅ **UUIDs** - Distributed-system ready

---

For full documentation, see `app/models/README.md` and `MODELS_SUMMARY.md`.

