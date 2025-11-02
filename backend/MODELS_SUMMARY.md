# Database Models - Final Implementation

## ✅ Complete Model List

**8 Core Models** (All with UUID Primary Keys):

1. **User** - Authentication and contributors
2. **Language** - Endangered languages
3. **Audio** - Audio recordings
4. **Document** - All text content (unified, no title)
5. **Location** - Geographic coordinates
6. **Tag** - Categorization
7. **Image** - Visual references
8. **Word** - Core vocabulary model

---

## ⭐ Key Feature: Typed Word-Document Relationships

Words have **specific typed relationships** to Documents:

```python
word.definitions           # Definition documents
word.literal_translations  # Literal translation documents
word.context_notes         # Context note documents
word.usage_examples        # Usage example documents
word.etymologies           # Etymology documents
word.cultural_significance # Cultural significance documents
word.documents             # ALL documents (generic)
```

---

## 📊 Model Details

### Document (Unified)

**No title field!** Typed by `document_type` enum instead.

**Fields:**
- `content` - The text (any size)
- `document_type` - Enum (story, definition, etymology, etc.)
- `language_id` - Optional (language of the content)
- `source`, `notes`

**Types:**
- **Full:** story, historical_record, book, article, transcription
- **Snippets:** definition, etymology, usage_example, cultural_significance, etc.

---

### Word (Core Model)

**21 Fields:**

*Core (5):*
- `id`, `word`, `romanization`, `ipa_pronunciation`, `language_id`

*Linguistic (6 - all enums):*
- `part_of_speech`, `gender`, `plurality`
- `grammatical_case`, `verb_aspect`, `animacy`

*Cultural/Location (2):*
- `register`, `confirmed_at_id`

*Metadata (6):*
- `created_by_id`, `verified_by_id`, `is_verified`
- `status`, `source`, `notes`

*Timestamps (2):*
- `created_at`, `updated_at`

**17 Relationships:**

1. `language` - Language (M:1)
2. `created_by` - User (M:1)
3. `verified_by` - User (M:1)
4. `confirmed_at` - Location (M:1)
5. `audio_files` - Audio (M:M)
6. `images` - Image (M:M)
7. `tags` - Tag (M:M)
8. **`definitions`** ⭐ - Document (M:M, typed)
9. **`literal_translations`** ⭐ - Document (M:M, typed)
10. **`context_notes`** ⭐ - Document (M:M, typed)
11. **`usage_examples`** ⭐ - Document (M:M, typed)
12. **`etymologies`** ⭐ - Document (M:M, typed)
13. **`cultural_significance`** ⭐ - Document (M:M, typed)
14. `documents` - Document (M:M, all types)
15. `synonyms` - Word (M:M self-ref)
16. `antonyms` - Word (M:M self-ref)
17. `related_words` - Word (M:M self-ref)

---

## 🎨 Enumerations (10 Total)

### Word Enums (8)
1. **PartOfSpeech** - 14 values
2. **GrammaticalGender** - 7 values
3. **Plurality** - 7 values
4. **GrammaticalCase** - 16 values
5. **VerbAspect** - 11 values
6. **Animacy** - 7 values
7. **Register** - 10 values
8. **WordStatus** - 5 values

### Document Enum (1)
9. **DocumentType** - 14 values

### Association Enum (1)
10. **WordDocumentType** ⭐ - 7 values (definition, etymology, etc.)

---

## 🗂️ Association Tables (6 Total)

1. **word_tags** - Word ↔ Tag
2. **word_audio** - Word ↔ Audio (`is_primary` flag)
3. **word_image** - Word ↔ Image (`is_primary` flag)
4. **word_documents** ⭐ - Word ↔ Document (**with `relationship_type`**)
5. **word_synonyms** - Word ↔ Word
6. **word_antonyms** - Word ↔ Word  
7. **word_related** - Word ↔ Word (`relationship_type` field)

---

## 📁 File Structure

```
backend/app/models/
  ├── user.py
  ├── language.py
  ├── audio.py
  ├── document.py        # Unified (no title)
  ├── location.py
  ├── image.py
  ├── tag.py
  └── word/              # Package
      ├── __init__.py
      ├── enums.py       # Linguistic enums
      ├── word.py        # Word model
      └── associations.py # WordDocumentType + tables
```

---

## 💡 Usage Example

```python
from app.models import Word, Document
from app.models.document import DocumentType
from app.models.word import WordDocumentType, word_documents
from sqlalchemy import insert

# Create word
word = Word(
    word="wəlapəmkanni",
    language_id=lang_id,
    created_by_id=user_id
)

# Create typed documents
definition = Document(
    content="good health, spiritual wellness",
    document_type=DocumentType.DEFINITION,
    created_by_id=user_id
)

etymology = Document(
    content="From wəli (good) + pemk (body) + anni (state)",
    document_type=DocumentType.ETYMOLOGY,
    created_by_id=user_id
)

example = Document(
    content="Nəmatta wəlapəmkanni - I wish you good health",
    document_type=DocumentType.USAGE_EXAMPLE,
    created_by_id=user_id
)

session.add_all([word, definition, etymology, example])
session.flush()

# Link with relationship types
session.execute(
    insert(word_documents).values([
        {
            "word_id": word.id,
            "document_id": definition.id,
            "relationship_type": WordDocumentType.DEFINITION
        },
        {
            "word_id": word.id,
            "document_id": etymology.id,
            "relationship_type": WordDocumentType.ETYMOLOGY
        },
        {
            "word_id": word.id,
            "document_id": example.id,
            "relationship_type": WordDocumentType.USAGE_EXAMPLE
        }
    ])
)

session.commit()

# Query with typed relationships
word = session.query(Word).options(
    joinedload(Word.definitions),
    joinedload(Word.etymologies),
    joinedload(Word.usage_examples)
).filter(Word.id == word_id).first()

# Access specific types
print("Definitions:")
for doc in word.definitions:
    print(f"  - {doc.content}")

print("\nEtymology:")
for doc in word.etymologies:
    print(f"  - {doc.content}")

print("\nExamples:")
for doc in word.usage_examples:
    print(f"  - {doc.content}")
```

---

## 🎯 Key Benefits

✅ **Unified Document** - One model for all text (no title field)  
✅ **Typed Relationships** - Easy access to specific document types  
✅ **Multiple Per Type** - Many definitions, etymologies, examples  
✅ **Type-Safe** - Enums everywhere  
✅ **Geographic Tracking** - Location model  
✅ **UUIDs** - Distributed-system ready  
✅ **No Linter Errors** - Clean, production-ready code

---

## 📚 Documentation

- **`QUICK_START.md`** - Quick reference
- **`TYPED_RELATIONSHIPS_GUIDE.md`** ⭐ - Detailed guide on typed relationships
- **`app/models/README.md`** - Full model documentation

---

## 🚀 Next Steps

1. **Create migration:**
```bash
alembic revision --autogenerate -m "Add typed word-document relationships"
alembic upgrade head
```

2. **Start using typed relationships!**

The database schema is complete and ready for endangered language preservation! 🌍
