# Word Model - Quick Field Reference

## Summary
A comprehensive model with **40+ fields** designed for endangered language preservation, capturing linguistic, cultural, educational, and metadata aspects of vocabulary.

---

## Field Categories (40 fields total)

### 🔑 Primary & Foreign Keys (5 fields)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | Integer | Yes | Primary key |
| `language_id` | FK → languages | Yes | Language reference |
| `audio_id` | FK → audio | No | Primary pronunciation audio |
| `created_by_id` | FK → users | Yes | Creator reference |
| `verified_by_id` | FK → users | No | Verifier reference |

---

### 📝 Core Word Data (4 fields)
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `word` | String(255) | Yes | ✓ | The actual word |
| `romanization` | String(255) | No | ✓ | Romanized form |
| `ipa_pronunciation` | String(255) | No | - | IPA transcription |
| `definition` | Text | Yes | - | Primary definition |

---

### 📚 Linguistic Properties (6 fields)
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `part_of_speech` | Enum | No | ✓ | noun, verb, adj., etc. |
| `gender` | Enum | No | - | Grammatical gender |
| `plurality` | Enum | No | - | Number distinction |
| `grammatical_case` | String(50) | No | - | Case marking |
| `verb_aspect` | String(50) | No | - | Verbal aspect |
| `animacy` | String(50) | No | - | Animate/inanimate |

---

### 💭 Meaning & Context (6 fields)
| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `literal_translation` | Text | Text | Word-for-word meaning |
| `context_notes` | Text | Text | Usage context |
| `usage_examples` | Text | JSON | Example sentences |
| `synonyms` | Text | JSON | Similar words |
| `antonyms` | Text | JSON | Opposite words |
| `related_words` | Text | JSON | Related vocabulary |

---

### 🎨 Cultural & Historical (4 fields)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `etymology` | Text | - | Word origin & history |
| `cultural_significance` | Text | - | Cultural importance |
| `register` | Enum | neutral | Formality level |
| `regional_variant` | String(255) | - | Dialect information |

---

### 🎓 Learning & Classification (5 fields)
| Field | Type | Required | Indexed | Description |
|-------|------|----------|---------|-------------|
| `difficulty_level` | Enum | No | ✓ | Learning difficulty |
| `frequency_rank` | Integer | No | - | Usage frequency |
| `category` | String(100) | No | ✓ | Semantic domain |
| `tags` | Text | No | - | Additional tags (JSON) |
| `is_endangered_specific` | Boolean | No | - | Unique to language |

---

### 🖼️ Media (1 field)
| Field | Type | Description |
|-------|------|-------------|
| `image_url` | String(500) | Visual reference URL |

---

### ✅ Quality & Workflow (5 fields)
| Field | Type | Default | Indexed | Description |
|-------|------|---------|---------|-------------|
| `is_verified` | Boolean | False | ✓ | Verification status |
| `status` | Enum | draft | ✓ | Publication state |
| `source` | String(500) | - | - | Documentation source |
| `notes` | Text | - | - | Internal notes |

---

### ⏰ Timestamps (2 fields)
| Field | Type | Auto | Description |
|-------|------|------|-------------|
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |

---

## Enumerations

### PartOfSpeech (14 values)
`noun`, `verb`, `adjective`, `adverb`, `pronoun`, `preposition`, `conjunction`, `interjection`, `article`, `determiner`, `particle`, `numeral`, `classifier`, `other`

### GrammaticalGender (7 values)
`masculine`, `feminine`, `neuter`, `common`, `animate`, `inanimate`, `not_applicable`

### Plurality (7 values)
`singular`, `plural`, `dual`, `trial`, `paucal`, `collective`, `not_applicable`

### Register (10 values)
`formal`, `informal`, `colloquial`, `slang`, `ceremonial`, `archaic`, `taboo`, `poetic`, `technical`, `neutral`

### DifficultyLevel (5 values)
`beginner`, `elementary`, `intermediate`, `advanced`, `native`

### WordStatus (5 values)
`draft`, `pending_review`, `published`, `deprecated`, `archived`

---

## Indexes (9 indexed fields)
Performance-optimized fields for common queries:
1. `word` - Fast word lookups
2. `language_id` - Filter by language
3. `romanization` - Search romanized versions
4. `part_of_speech` - Grammatical filtering
5. `difficulty_level` - Learning level
6. `category` - Semantic domain
7. `is_verified` - Verified content
8. `status` - Publication status
9. `id` - Primary key (automatic)

---

## JSON Field Structures

### `usage_examples`
```json
[
  {
    "example": "Native language sentence",
    "translation": "English translation",
    "context": "When this is used (optional)"
  }
]
```

### `tags`
```json
["tag1", "tag2", "tag3"]
```

### `synonyms` / `antonyms`
```json
["word1", "word2"]  // or [123, 456] for word IDs
```

### `related_words`
```json
[
  {"id": 123, "relationship": "derived_from"},
  {"id": 456, "relationship": "compound_part"}
]
```

---

## Required vs Optional

### ✅ Required Fields (5)
1. `word` - The word itself
2. `language_id` - Must belong to a language
3. `definition` - Must have meaning
4. `created_by_id` - Track who created it
5. `created_at` / `updated_at` - Automatic timestamps

### ⭕ Everything Else Optional (35+ fields)
This flexibility allows:
- Quick entry of basic words
- Gradual enrichment over time
- Community contributions at various expertise levels

---

## Common Query Patterns

### By Language
```sql
WHERE language_id = ? AND status = 'published'
```

### By Learning Level
```sql
WHERE difficulty_level = 'beginner' AND is_verified = true
```

### By Category
```sql
WHERE category = 'animals' AND language_id = ?
```

### Search
```sql
WHERE (word LIKE ? OR romanization LIKE ? OR definition LIKE ?)
```

### Unverified Content
```sql
WHERE is_verified = false AND status = 'pending_review'
```

---

## Size Estimates

### Minimal Entry (~200 bytes)
- Required fields only
- Word, definition, language, metadata

### Average Entry (~1-2 KB)
- Basic linguistic info
- Some context and examples
- Audio link

### Comprehensive Entry (~5-10 KB)
- All linguistic details
- Multiple examples
- Etymology, cultural notes
- Full metadata

### With Media (varies)
- Image URLs: add ~100 bytes
- Audio files: separate table
- Usage examples: ~100-500 bytes per example

---

## Scalability Considerations

### Expected Scale
- Small endangered language: 500-5,000 words
- Medium language: 5,000-50,000 words  
- Large dictionary: 50,000-500,000 words

### Database Size Estimate
- 10,000 words × 2 KB avg = ~20 MB
- 100,000 words × 2 KB avg = ~200 MB
- Indexes: ~10-20% additional space

### Performance
- All critical fields indexed
- Efficient for filtering, sorting, searching
- Pagination recommended for large result sets

---

## Validation Rules (in Schemas)

### String Lengths
- `word`, `romanization`, `ipa_pronunciation`: max 255
- `grammatical_case`, `verb_aspect`, `animacy`: max 50
- `category`: max 100
- `regional_variant`: max 255
- `image_url`, `source`: max 500
- Text fields: unlimited

### Numeric Constraints
- All IDs: > 0
- `frequency_rank`: > 0 (if set)

### Required Fields
- `word`: min 1 character
- `definition`: min 1 character
- `language_id`: must exist

---

## Workflow States

```
DRAFT → PENDING_REVIEW → PUBLISHED
   ↓           ↓              ↓
ARCHIVED   DEPRECATED     DEPRECATED
```

### State Meanings
- **DRAFT**: Work in progress, not public
- **PENDING_REVIEW**: Submitted for verification
- **PUBLISHED**: Verified and publicly visible
- **DEPRECATED**: Outdated or incorrect
- **ARCHIVED**: Historical record only

---

## Related Models Required

This Word model expects relationships with:

1. **Language** model
   - `back_populates="words"`

2. **User** model
   - `back_populates="words_created"`
   - `back_populates="words_verified"`

3. **Audio** model
   - Foreign key relationship

Ensure these models have the corresponding relationship definitions.

