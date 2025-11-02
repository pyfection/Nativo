# Word Model Documentation

## Overview

The `Word` model is designed for comprehensive language preservation, capturing not just vocabulary but the linguistic, cultural, and contextual richness of endangered languages.

## Model Structure

### Core Fields

#### `id` (Integer, Primary Key)
- Unique identifier for each word entry

#### `word` (String, required)
- The actual word in the target language
- Indexed for fast searching
- Max length: 255 characters

#### `language_id` (Integer, Foreign Key, required)
- References the Language table
- Indexed for efficient queries by language

#### `romanization` (String, optional)
- Romanized or transliterated version of the word
- Essential for non-Latin scripts (Arabic, Chinese, etc.)
- Indexed for searching
- Example: Japanese "ありがとう" → "arigatou"

#### `ipa_pronunciation` (String, optional)
- International Phonetic Alphabet representation
- Provides standardized pronunciation guide
- Example: "water" → /ˈwɔːtər/

---

### Linguistic Information

#### `part_of_speech` (Enum, optional)
Options:
- `noun`, `verb`, `adjective`, `adverb`, `pronoun`
- `preposition`, `conjunction`, `interjection`
- `article`, `determiner`, `particle`, `numeral`, `classifier`
- `other`

#### `gender` (Enum, optional)
Grammatical gender categories:
- `masculine`, `feminine`, `neuter`, `common`
- `animate`, `inanimate`, `not_applicable`

#### `plurality` (Enum, optional)
Number distinctions:
- `singular`, `plural`, `dual` (for languages with dual forms)
- `trial`, `paucal`, `collective`
- `not_applicable`

#### `grammatical_case` (String, optional)
- For inflected languages (e.g., nominative, accusative, genitive, dative)
- Free-text field to accommodate various case systems

#### `verb_aspect` (String, optional)
- Perfective, imperfective, progressive, habitual, etc.
- Particularly important for Slavic and many endangered languages

#### `animacy` (String, optional)
- Animate vs. inanimate distinction
- Important in languages like Navajo, Ojibwe, etc.

---

### Meaning & Context

#### `definition` (Text, required)
- Primary definition of the word
- Can be in English or another lingua franca
- Should be clear and comprehensive

#### `literal_translation` (Text, optional)
- Word-for-word or morpheme-by-morpheme translation
- Example: German "Handschuh" → "hand-shoe" (glove)

#### `context_notes` (Text, optional)
- Cultural or contextual information
- When and how the word is used
- Social contexts, taboos, special occasions

#### `usage_examples` (Text, optional)
- JSON array of example sentences
- Shows the word in natural context
- Format: `[{"example": "sentence", "translation": "meaning"}]`

#### `synonyms`, `antonyms`, `related_words` (Text, optional)
- JSON arrays storing related vocabulary
- Can reference word IDs or actual words
- Builds a semantic network

---

### Audio & Media

#### `audio_id` (Integer, Foreign Key, optional)
- Links to the primary pronunciation audio file
- Essential for preserving phonetics of endangered languages

#### `image_url` (String, optional)
- Visual reference for the word
- Helpful for concrete nouns (animals, objects, etc.)
- Max length: 500 characters

---

### Etymology & Cultural Context

#### `etymology` (Text, optional)
- Origin and historical development of the word
- Borrowings from other languages
- Historical sound changes

#### `cultural_significance` (Text, optional)
- Cultural importance or traditional usage
- Sacred terms, ceremonial language
- Cultural concepts unique to the language community

#### `register` (Enum, optional)
Formality and usage levels:
- `formal`, `informal`, `colloquial`, `slang`
- `ceremonial`, `archaic`, `taboo`, `poetic`
- `technical`, `neutral` (default)

#### `regional_variant` (String, optional)
- Dialect or regional information
- Geographic variations
- Different pronunciations by region

---

### Learning & Classification

#### `difficulty_level` (Enum, optional)
For language learners:
- `beginner`, `elementary`, `intermediate`, `advanced`, `native`

#### `frequency_rank` (Integer, optional)
- How commonly the word is used
- Lower number = more frequent
- Helps learners prioritize vocabulary

#### `category` (String, optional)
Semantic domains:
- `nature`, `family`, `food`, `religion`, `animals`
- `body_parts`, `numbers`, `colors`, `tools`, etc.
- Indexed for browsing by topic

#### `tags` (Text, optional)
- JSON array of additional classification tags
- Flexible categorization system
- Format: `["agricultural", "seasonal", "traditional"]`

#### `is_endangered_specific` (Boolean)
- Flags words unique to this endangered language
- Concepts that may not exist in dominant languages
- Important for cultural preservation
- Default: `False`

---

### Metadata & Quality Control

#### `created_by_id` (Integer, Foreign Key, required)
- User who added the word entry
- Tracks contributions

#### `verified_by_id` (Integer, Foreign Key, optional)
- Expert or native speaker who verified the entry
- Null if not yet verified

#### `is_verified` (Boolean)
- Quick flag for verification status
- Indexed for filtering verified content
- Default: `False`

#### `status` (Enum)
Publication workflow:
- `draft` - Initial entry, work in progress
- `pending_review` - Submitted for verification
- `published` - Verified and publicly visible
- `deprecated` - Outdated or incorrect
- `archived` - Historical record only

#### `source` (String, optional)
- Documentation source
- "Elder John Smith, interview 2024-03-15"
- "Historical dictionary page 42"
- Max length: 500 characters

#### `notes` (Text, optional)
- Internal notes for editors and reviewers
- Questions, concerns, areas needing clarification

---

### Timestamps

#### `created_at` (DateTime)
- When the entry was first created
- Auto-set on creation

#### `updated_at` (DateTime)
- Last modification timestamp
- Auto-updated on any change

---

## Relationships

### Language
```python
language = relationship("Language", back_populates="words")
```
- Each word belongs to one language
- Language can have many words

### Audio
```python
audio = relationship("Audio", foreign_keys=[audio_id])
```
- Optional link to pronunciation audio
- One-to-one relationship for primary audio

### Users (Created By)
```python
created_by = relationship("User", foreign_keys=[created_by_id], back_populates="words_created")
```
- Tracks who created the entry

### Users (Verified By)
```python
verified_by = relationship("User", foreign_keys=[verified_by_id], back_populates="words_verified")
```
- Tracks expert verification

---

## Usage Examples

### Creating a Basic Word Entry

```python
from app.models.word import Word, PartOfSpeech, Register, WordStatus

word = Word(
    word="wapiti",
    language_id=1,  # Shawnee language
    part_of_speech=PartOfSpeech.NOUN,
    definition="elk, deer",
    is_endangered_specific=True,
    created_by_id=1,
    status=WordStatus.DRAFT
)
```

### Creating a Comprehensive Entry

```python
import json

word = Word(
    # Core
    word="Schadenfreude",
    language_id=2,  # German
    ipa_pronunciation="/ˈʃaːdənˌfʁɔʏ̯də/",
    
    # Linguistic
    part_of_speech=PartOfSpeech.NOUN,
    gender=GrammaticalGender.FEMININE,
    plurality=Plurality.SINGULAR,
    
    # Meaning
    definition="pleasure derived from another person's misfortune",
    literal_translation="harm-joy",
    context_notes="Often used in psychology and philosophy",
    usage_examples=json.dumps([
        {
            "german": "Er empfand Schadenfreude, als sein Rivale verlor.",
            "english": "He felt schadenfreude when his rival lost."
        }
    ]),
    
    # Classification
    difficulty_level=DifficultyLevel.ADVANCED,
    category="emotion",
    register=Register.FORMAL,
    
    # Metadata
    created_by_id=1,
    status=WordStatus.PUBLISHED,
    is_verified=True
)
```

### Creating an Entry for Non-Latin Script

```python
word = Word(
    word="ありがとう",
    romanization="arigatou",
    ipa_pronunciation="/aɾiɡatoː/",
    language_id=3,  # Japanese
    
    part_of_speech=PartOfSpeech.INTERJECTION,
    definition="thank you",
    literal_translation="it is difficult to exist",
    
    etymology="From 'arigatashi' (有難し), meaning rare or precious",
    register=Register.INFORMAL,
    
    difficulty_level=DifficultyLevel.BEGINNER,
    frequency_rank=10,
    
    created_by_id=1
)
```

### Querying Words

```python
# Find all nouns in a language
nouns = session.query(Word).filter(
    Word.language_id == 1,
    Word.part_of_speech == PartOfSpeech.NOUN,
    Word.status == WordStatus.PUBLISHED
).all()

# Find verified words for beginners
beginner_words = session.query(Word).filter(
    Word.difficulty_level == DifficultyLevel.BEGINNER,
    Word.is_verified == True
).all()

# Search by romanization
words = session.query(Word).filter(
    Word.romanization.ilike('%search_term%')
).all()

# Find endangered-specific words
unique_words = session.query(Word).filter(
    Word.is_endangered_specific == True,
    Word.status == WordStatus.PUBLISHED
).all()
```

---

## Best Practices

### 1. **Always Provide Context**
- Don't just list words - explain how they're used
- Include usage examples whenever possible
- Note cultural significance

### 2. **Get Native Speaker Verification**
- Mark entries as `is_verified` only after expert review
- Use `verified_by_id` to track who confirmed the entry
- Document the source of information

### 3. **Use Standardized Systems**
- IPA for pronunciation
- Consistent romanization schemes
- Standard linguistic terminology

### 4. **Capture What's Unique**
- Flag `is_endangered_specific` for unique concepts
- Document cultural significance
- Record etymology and historical context

### 5. **Support Learning**
- Add difficulty levels
- Categorize by semantic domain
- Include frequency information

### 6. **Build Relationships**
- Link synonyms and antonyms
- Connect related words
- Create semantic networks

---

## JSON Field Formats

### `usage_examples`
```json
[
  {
    "example": "Sentence in target language",
    "translation": "English translation",
    "context": "Optional context note"
  }
]
```

### `tags`
```json
["tag1", "tag2", "tag3"]
```

### `synonyms` / `antonyms`
```json
["word1", "word2"]
```
or
```json
[123, 456]  // Word IDs
```

### `related_words`
```json
[
  {"id": 123, "relationship": "derived_from"},
  {"id": 456, "relationship": "compound_part"}
]
```

---

## Database Indexes

The following fields are indexed for performance:
- `word` - Fast word lookups
- `language_id` - Filter by language
- `romanization` - Search romanized forms
- `part_of_speech` - Filter by grammatical category
- `difficulty_level` - Filter by learning level
- `category` - Browse by semantic domain
- `is_verified` - Show only verified content
- `status` - Filter by publication status

---

## Future Enhancements

Potential additions to consider:

1. **Morphology Table** - Detailed inflection patterns
2. **Pronunciation Variants** - Multiple audio files for dialects
3. **Historical Forms** - Track language evolution
4. **Cognates** - Links to words in related languages
5. **Visual Annotations** - Images with labeled parts
6. **Usage Statistics** - Track how often words are studied
7. **Community Ratings** - User feedback on definitions
8. **Derivation Trees** - Morphological relationships

---

## Migration Considerations

When creating the database migration for this model, ensure:

1. All enums are properly created
2. Foreign key constraints are set up
3. Indexes are created for performance
4. Default values are applied
5. Relationships in Language, User, and Audio models are updated

Example migration command:
```bash
alembic revision --autogenerate -m "Create comprehensive word model"
alembic upgrade head
```

