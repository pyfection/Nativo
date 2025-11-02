# Typed Word-Document Relationships Guide

## Overview

Words now have **typed relationships** to Documents, making it easy to access specific types of information.

---

## The Relationships

Each word can have multiple documents of each type:

- **`word.definitions`** - Definition documents
- **`word.literal_translations`** - Literal translation documents
- **`word.context_notes`** - Context note documents
- **`word.usage_examples`** - Usage example documents
- **`word.etymologies`** - Etymology documents  
- **`word.cultural_significance`** - Cultural significance documents
- **`word.documents`** - ALL documents (including stories where word is mentioned)

---

## How It Works

### Under the Hood

The `word_documents` association table has a `relationship_type` field:

```sql
CREATE TABLE word_documents (
    word_id UUID,
    document_id UUID,
    relationship_type VARCHAR (enum),  -- 'definition', 'etymology', etc.
    created_at TIMESTAMP,
    PRIMARY KEY (word_id, document_id, relationship_type)
);
```

### WordDocumentType Enum

```python
class WordDocumentType(str, enum.Enum):
    DEFINITION = "definition"
    LITERAL_TRANSLATION = "literal_translation"
    CONTEXT_NOTE = "context_note"
    USAGE_EXAMPLE = "usage_example"
    ETYMOLOGY = "etymology"
    CULTURAL_SIGNIFICANCE = "cultural_significance"
    OTHER = "other"
```

---

## Usage Examples

### Creating Typed Relationships

```python
from app.models import Word, Document
from app.models.document import DocumentType
from app.models.word import WordDocumentType
from sqlalchemy import insert

# Create word
word = Word(
    word="wəlapəmkanni",
    language_id=lang_id,
    created_by_id=user_id
)
session.add(word)

# Create definition document
definition1 = Document(
    content="good health, spiritual wellness",
    document_type=DocumentType.DEFINITION,
    source="Elder Interview 2024",
    created_by_id=user_id
)

definition2 = Document(
    content="state of holistic wellbeing",
    document_type=DocumentType.DEFINITION,
    source="Dictionary 1890",
    created_by_id=user_id
)

# Create etymology document
etymology = Document(
    content="From wəli (good) + pemk (body) + anni (state)",
    document_type=DocumentType.ETYMOLOGY,
    source="Linguistic Research",
    created_by_id=user_id
)

# Create usage example
example = Document(
    content="Nəmatta wəlapəmkanni - I wish you good health",
    document_type=DocumentType.USAGE_EXAMPLE,
    created_by_id=user_id
)

session.add_all([definition1, definition2, etymology, example])
session.flush()  # Get IDs

# Link with specific relationship types
from app.models.word import word_documents

session.execute(
    insert(word_documents).values([
        {
            "word_id": word.id,
            "document_id": definition1.id,
            "relationship_type": WordDocumentType.DEFINITION
        },
        {
            "word_id": word.id,
            "document_id": definition2.id,
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
```

### Querying Typed Relationships

```python
from sqlalchemy.orm import joinedload

# Get word with all typed relationships loaded
word = session.query(Word).options(
    joinedload(Word.definitions),
    joinedload(Word.etymologies),
    joinedload(Word.usage_examples),
    joinedload(Word.literal_translations),
    joinedload(Word.context_notes),
    joinedload(Word.cultural_significance)
).filter(Word.id == word_id).first()

# Access typed relationships
print("Definitions:")
for doc in word.definitions:
    print(f"  - {doc.content} (source: {doc.source})")

print("\nEtymologies:")
for doc in word.etymologies:
    print(f"  - {doc.content}")

print("\nUsage Examples:")
for doc in word.usage_examples:
    print(f"  - {doc.content}")
```

### API Helper Function

```python
def add_word_document(
    session,
    word_id: UUID,
    document_id: UUID,
    relationship_type: WordDocumentType
):
    """Helper to add a typed word-document relationship"""
    from app.models.word import word_documents
    from sqlalchemy import insert
    
    session.execute(
        insert(word_documents).values(
            word_id=word_id,
            document_id=document_id,
            relationship_type=relationship_type
        )
    )
    session.commit()

# Usage
add_word_document(
    session,
    word.id,
    definition_doc.id,
    WordDocumentType.DEFINITION
)
```

---

## Benefits

### ✅ Type-Safe Access

```python
# OLD: Generic list, unclear what's what
for doc in word.documents:
    # Is this a definition? Etymology? Who knows!
    print(doc.content)

# NEW: Clear and specific
for definition in word.definitions:
    print(f"Definition: {definition.content}")
    
for etymology in word.etymologies:
    print(f"Etymology: {etymology.content}")
```

### ✅ Easy Querying

```python
# Get only definitions
definitions = word.definitions

# Get only etymologies
etymologies = word.etymologies

# Get all documents (any type)
all_docs = word.documents
```

### ✅ Multiple Per Type

Each word can have:
- Multiple definitions (from different sources)
- Multiple usage examples
- Multiple etymologies (from different scholars)
- Multiple context notes

```python
# Word with 3 definitions from different time periods
for definition in word.definitions:
    print(f"{definition.source}: {definition.content}")

# Output:
# Dictionary 1890: state of physical health
# Elder Interview 1950: spiritual and physical harmony
# Modern Definition 2024: holistic wellness encompassing mind, body, spirit
```

---

## Real-World Example

### Creating a Rich Word Entry

```python
from app.models import Word, Document
from app.models.document import DocumentType
from app.models.word import WordDocumentType, word_documents
from sqlalchemy import insert

# Create the word
word = Word(
    word="Schadenfreude",
    romanization="Schadenfreude",
    ipa_pronunciation="/ˈʃaːdənˌfʁɔʏ̯də/",
    language_id=german_id,
    created_by_id=user_id
)

# Create multiple definitions
def_psych = Document(
    content="pleasure derived from another person's misfortune",
    document_type=DocumentType.DEFINITION,
    source="Psychology Textbook 2020",
    created_by_id=user_id
)

def_phil = Document(
    content="malicious joy at others' suffering",
    document_type=DocumentType.DEFINITION,
    source="Philosophy Dictionary 1985",
    created_by_id=user_id
)

# Literal translation
literal = Document(
    content="harm-joy",
    document_type=DocumentType.LITERAL_TRANSLATION,
    created_by_id=user_id
)

# Etymology
etymology = Document(
    content="From German 'Schaden' (harm, damage) + 'Freude' (joy, pleasure)",
    document_type=DocumentType.ETYMOLOGY,
    source="Oxford Etymology Dictionary",
    created_by_id=user_id
)

# Cultural significance
cultural = Document(
    content="Concept explored extensively in Nietzsche's philosophy",
    document_type=DocumentType.CULTURAL_SIGNIFICANCE,
    source="Nietzsche Studies",
    created_by_id=user_id
)

# Usage examples
example1 = Document(
    content="Er empfand Schadenfreude, als sein Rivale verlor",
    document_type=DocumentType.USAGE_EXAMPLE,
    created_by_id=user_id
)

session.add_all([
    word, def_psych, def_phil, literal, 
    etymology, cultural, example1
])
session.flush()

# Link them with types
session.execute(
    insert(word_documents).values([
        {"word_id": word.id, "document_id": def_psych.id, 
         "relationship_type": WordDocumentType.DEFINITION},
        {"word_id": word.id, "document_id": def_phil.id, 
         "relationship_type": WordDocumentType.DEFINITION},
        {"word_id": word.id, "document_id": literal.id, 
         "relationship_type": WordDocumentType.LITERAL_TRANSLATION},
        {"word_id": word.id, "document_id": etymology.id, 
         "relationship_type": WordDocumentType.ETYMOLOGY},
        {"word_id": word.id, "document_id": cultural.id, 
         "relationship_type": WordDocumentType.CULTURAL_SIGNIFICANCE},
        {"word_id": word.id, "document_id": example1.id, 
         "relationship_type": WordDocumentType.USAGE_EXAMPLE},
    ])
)

session.commit()
```

### Displaying the Word

```python
# Later: display the word with all its information
word = session.query(Word).options(
    joinedload(Word.definitions),
    joinedload(Word.literal_translations),
    joinedload(Word.etymologies),
    joinedload(Word.cultural_significance),
    joinedload(Word.usage_examples)
).filter(Word.word == "Schadenfreude").first()

print(f"Word: {word.word}")
print(f"IPA: {word.ipa_pronunciation}")

print("\nDefinitions:")
for def_doc in word.definitions:
    print(f"  • {def_doc.content}")
    print(f"    Source: {def_doc.source}")

if word.literal_translations:
    print(f"\nLiteral: {word.literal_translations[0].content}")

if word.etymologies:
    print(f"\nEtymology: {word.etymologies[0].content}")

if word.cultural_significance:
    print(f"\nCultural: {word.cultural_significance[0].content}")

print("\nExamples:")
for ex in word.usage_examples:
    print(f"  • {ex.content}")
```

**Output:**
```
Word: Schadenfreude
IPA: /ˈʃaːdənˌfʁɔʏ̯də/

Definitions:
  • pleasure derived from another person's misfortune
    Source: Psychology Textbook 2020
  • malicious joy at others' suffering
    Source: Philosophy Dictionary 1985

Literal: harm-joy

Etymology: From German 'Schaden' (harm, damage) + 'Freude' (joy, pleasure)

Cultural: Concept explored extensively in Nietzsche's philosophy

Examples:
  • Er empfand Schadenfreude, als sein Rivale verlor
```

---

## Migration Note

When you create the migration, the composite primary key will be:
- `word_id`
- `document_id`
- `relationship_type`

This means the same word-document pair can have multiple relationship types if needed (though typically you'd use one type per pair).

---

## Summary

✅ **Typed relationships** for clear access to specific document types  
✅ **Multiple per type** - many definitions, examples, etymologies  
✅ **Type-safe** - Use enums, not strings  
✅ **Easy to query** - `word.definitions` instead of filtering  
✅ **Backward compatible** - `word.documents` still gives you everything

This makes it much easier to build rich word entries with well-organized information from multiple sources!

