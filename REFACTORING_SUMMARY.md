# Document to Text Refactoring Summary

## Overview

This refactoring splits the `Document` model into two models to support translations:

1. **Text** - Stores actual content with a title, in specific languages
2. **Document** - Groups Text records (translations of the same content)

## Changes Implemented

### Backend Models ✅

1. **Created `app/models/text.py`**
   - Renamed from Document model
   - Added `title` field (required, max 500 chars)
   - Added `is_primary` field (boolean, default False)
   - Added `document_id` FK (links to parent Document)
   - Table name: `texts`

2. **Updated `app/models/document.py`**
   - Simplified to just group texts
   - Fields: `id`, `created_by_id`, `created_at`, `updated_at`
   - Relationship: `texts` (one-to-many with Text)
   - Table name: `documents`

3. **Updated `app/models/word/associations.py`**
   - Renamed `word_documents` → `word_texts` (for language-specific content)
   - Renamed `WordDocumentType` → `WordTextType`
   - Removed Document-level types (definition, etymology, cultural_significance)
   - Created `word_definitions` table (Word ↔ Document, many-to-many)

4. **Updated `app/models/word/word.py`**
   - Added FKs: `etymology_document_id`, `cultural_significance_document_id`
   - **Document-level relationships** (same across translations):
     - `definitions` → Document (many-to-many via `word_definitions`)
     - `etymology` → Document (one-to-one via FK)
     - `cultural_significance` → Document (one-to-one via FK)
   - **Text-level relationships** (language-specific):
     - `literal_translations` → Text
     - `context_notes` → Text
     - `usage_examples` → Text

5. **Updated `app/models/language.py`**
   - Changed `documents` relationship → `texts`

### Backend Schemas ✅

1. **Created `app/schemas/text.py`**
   - `TextBase`, `TextCreate`, `TextUpdate`, `TextInDB`, `Text`
   - `TextListItem`, `TextFilter`, `TextStatistics`

2. **Updated `app/schemas/document.py`**
   - Simplified schemas for new Document model
   - `DocumentWithTexts` - includes all translations
   - `DocumentListItem` - shows selected language text

### Database Migration ✅

Created `backend/alembic/versions/d4e5f6g7h8i9_refactor_document_to_text_with_translations.py`

**Migration steps:**
1. Renames `documents` → `texts`
2. Adds `title`, `is_primary`, `document_id` columns
3. Creates new `documents` table
4. Creates a Document for each existing Text (1:1 migration)
5. Auto-generates titles based on document_type
6. Renames `word_documents` → `word_texts`
7. Updates enum `WordDocumentType` → `WordTextType`
8. Creates `word_definitions` table
9. Adds FKs to words table

### Backend Admin ✅

Updated `app/admin.py`:
- Added `TextAdmin` view
- Updated `DocumentAdmin` view

### Frontend Types ✅

1. **Created `frontend/src/types/text.ts`**
   - `Text`, `TextListItem`, `TextCreate`, `TextUpdate`
   - `DocumentType` enum
   - `TextFilter`, `TextStatistics`

2. **Created `frontend/src/types/document.ts`**
   - `Document`, `DocumentWithTexts`, `DocumentListItem`
   - `DocumentFilter`, `DocumentStatistics`

### Frontend Service ✅

Updated `frontend/src/services/documentService.ts`:
- `getAll()` - fetches documents with text in selected language
- `getById()` - fetches document with all translations
- `getByIdForLanguage()` - gets specific language version
- `create()` - creates document with initial text
- `addTranslation()` - adds translation to document
- `updateText()` - updates specific text
- `deleteText()` - deletes specific translation

### Exports & Imports ✅

1. Updated `backend/app/models/__init__.py`
2. Updated `backend/app/models/word/__init__.py`
3. Updated `backend/alembic/env.py`

## What Still Needs Implementation

### Backend API Endpoints ⚠️

`backend/app/api/v1/endpoints/documents.py` needs to be implemented:

```python
# Required endpoints:
GET    /api/v1/documents/                    # List with language filtering
GET    /api/v1/documents/{id}                # Get with all texts
GET    /api/v1/documents/{id}/language/{lang_id}  # Get for specific language
POST   /api/v1/documents/                    # Create with initial text
POST   /api/v1/documents/{id}/texts          # Add translation
PUT    /api/v1/documents/{id}/texts/{text_id}  # Update text
DELETE /api/v1/documents/{id}                # Delete document
DELETE /api/v1/documents/{id}/texts/{text_id}  # Delete text
```

**Key logic:**
- When listing documents, return the text in the user's selected language
- If selected language not available, fall back to primary text
- DocumentListItem should include `title` from the selected text

### Frontend Components ⚠️

The following components need updates to use the new service:

1. `frontend/src/pages/DocumentList.tsx`
2. `frontend/src/pages/Documents.tsx`
3. `frontend/src/pages/AddDocument.tsx`
4. `frontend/src/components/documents/DocumentList.tsx`
5. `frontend/src/components/documents/DocumentViewer.tsx`
6. `frontend/src/components/documents/DocumentUpload.tsx`
7. `frontend/src/hooks/useDocuments.ts`

**Changes needed:**
- Use `documentService.getAll()` with language_id param
- Display `title` instead of truncated content
- Show translation count
- Add UI for adding/viewing translations
- Handle language selection context

### Documentation ⚠️

Update these files:
- `backend/app/models/README.md`
- `backend/MODELS_SUMMARY.md`
- `backend/QUICK_START.md`
- `backend/TYPED_RELATIONSHIPS_GUIDE.md`

## Running the Migration

```bash
cd backend
alembic upgrade head
```

## Key Design Decisions

1. **Title is required** - Even snippets need titles (auto-generated like "Definition", "Etymology")
2. **Primary flag on Text** - Marks the original/main translation
3. **Document groups translations** - Same content in different languages
4. **Separation of concerns**:
   - Document-level: definitions, etymology, cultural_significance (same meaning across languages)
   - Text-level: usage examples, context notes, literal translations (language-specific)

## Benefits

1. ✅ Full translation support
2. ✅ Better organization of multilingual content
3. ✅ Clearer separation between content types
4. ✅ Maintains backward compatibility through migration
5. ✅ Type-safe relationships between Words and Documents/Texts

