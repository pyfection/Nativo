"""refactor_document_to_text_with_translations

Revision ID: d4e5f6g7h8i9
Revises: 33151565d1c2
Create Date: 2025-11-03 00:00:00.000000

This migration refactors the Document model into two models:
1. Text - stores actual content with title, in specific languages
2. Document - groups Text records (translations)

Changes:
- Renames 'documents' table to 'texts'
- Adds 'title', 'is_primary', 'document_id' columns to texts
- Creates new 'documents' table
- Renames 'word_documents' association table to 'word_texts'
- Creates 'word_definitions' association table
- Adds foreign keys to words table for etymology and cultural_significance
- Migrates existing data
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = '33151565d1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Rename documents table to texts
    op.rename_table('documents', 'texts')
    
    # Step 2: Add new columns to texts table
    op.add_column('texts', sa.Column('title', sa.String(length=500), nullable=True))
    op.add_column('texts', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('texts', sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Step 3: Create new documents table
    op.create_table('documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 4: Migrate existing data - create Document for each Text
    connection = op.get_bind()
    
    # Get all existing texts
    result = connection.execute(text("""
        SELECT id, created_by_id, created_at, updated_at 
        FROM texts
    """))
    
    for row in result:
        text_id = row[0]
        created_by_id = row[1]
        created_at = row[2]
        updated_at = row[3]
        
        # Create a new document
        doc_id = connection.execute(text("""
            INSERT INTO documents (id, created_by_id, created_at, updated_at)
            VALUES (gen_random_uuid(), :created_by_id, :created_at, :updated_at)
            RETURNING id
        """), {"created_by_id": created_by_id, "created_at": created_at, "updated_at": updated_at}).scalar()
        
        # Link the text to the document
        connection.execute(text("""
            UPDATE texts 
            SET document_id = :doc_id
            WHERE id = :text_id
        """), {"doc_id": doc_id, "text_id": text_id})
    
    # Step 5: Auto-generate titles for existing texts
    # For texts linked to words, try to generate meaningful titles
    connection.execute(text("""
        UPDATE texts t
        SET title = CASE 
            WHEN document_type = 'definition' THEN 'Definition'
            WHEN document_type = 'literal_translation' THEN 'Literal Translation'
            WHEN document_type = 'context_note' THEN 'Context Note'
            WHEN document_type = 'usage_example' THEN 'Usage Example'
            WHEN document_type = 'etymology' THEN 'Etymology'
            WHEN document_type = 'cultural_significance' THEN 'Cultural Significance'
            WHEN document_type = 'story' THEN 'Story'
            WHEN document_type = 'historical_record' THEN 'Historical Record'
            WHEN document_type = 'book' THEN 'Book'
            WHEN document_type = 'article' THEN 'Article'
            WHEN document_type = 'transcription' THEN 'Transcription'
            WHEN document_type = 'translation' THEN 'Translation'
            WHEN document_type = 'note' THEN 'Note'
            ELSE SUBSTRING(content FROM 1 FOR 50) || 
                 CASE WHEN LENGTH(content) > 50 THEN '...' ELSE '' END
        END
        WHERE title IS NULL
    """))
    
    # Step 6: Make title NOT NULL after population
    op.alter_column('texts', 'title', nullable=False)
    
    # Step 7: Add foreign key constraint for document_id
    op.create_foreign_key('texts_document_id_fkey', 'texts', 'documents', ['document_id'], ['id'])
    op.create_index(op.f('ix_texts_document_id'), 'texts', ['document_id'], unique=False)
    
    # Step 8: Rename word_documents to word_texts and update structure
    op.rename_table('word_documents', 'word_texts_temp')
    
    # Update enum name for relationship types
    op.execute("ALTER TYPE worddocumenttype RENAME TO wordtexttype")
    
    # Remove values that are no longer in the enum
    op.execute("""
        DELETE FROM word_texts_temp 
        WHERE relationship_type IN ('definition', 'etymology', 'cultural_significance')
    """)
    
    # Update enum to only include text-level relationship types
    op.execute("ALTER TYPE wordtexttype RENAME TO wordtexttype_old")
    op.execute("""
        CREATE TYPE wordtexttype AS ENUM (
            'literal_translation', 'context_note', 'usage_example', 'other'
        )
    """)
    op.execute("""
        ALTER TABLE word_texts_temp 
        ALTER COLUMN relationship_type TYPE wordtexttype 
        USING relationship_type::text::wordtexttype
    """)
    op.execute("DROP TYPE wordtexttype_old")
    
    # Rename columns in the association table
    op.alter_column('word_texts_temp', 'document_id', new_column_name='text_id')
    
    # Update foreign key
    op.drop_constraint('word_documents_document_id_fkey', 'word_texts_temp', type_='foreignkey')
    op.create_foreign_key('word_texts_text_id_fkey', 'word_texts_temp', 'texts', ['text_id'], ['id'])
    
    # Rename table to final name
    op.rename_table('word_texts_temp', 'word_texts')
    
    # Step 9: Create word_definitions association table
    op.create_table('word_definitions',
        sa.Column('word_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ),
        sa.PrimaryKeyConstraint('word_id', 'document_id')
    )
    
    # Step 10: Add foreign keys to words table for one-to-one relationships
    op.add_column('words', sa.Column('etymology_document_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('words', sa.Column('cultural_significance_document_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    op.create_foreign_key('words_etymology_document_id_fkey', 'words', 'documents', ['etymology_document_id'], ['id'])
    op.create_foreign_key('words_cultural_significance_document_id_fkey', 'words', 'documents', ['cultural_significance_document_id'], ['id'])


def downgrade() -> None:
    # This is a complex migration, downgrade would be complicated
    # For now, we'll provide a basic downgrade that removes new structures
    
    # Remove foreign keys from words
    op.drop_constraint('words_cultural_significance_document_id_fkey', 'words', type_='foreignkey')
    op.drop_constraint('words_etymology_document_id_fkey', 'words', type_='foreignkey')
    op.drop_column('words', 'cultural_significance_document_id')
    op.drop_column('words', 'etymology_document_id')
    
    # Drop word_definitions table
    op.drop_table('word_definitions')
    
    # Rename word_texts back to word_documents
    op.rename_table('word_texts', 'word_documents')
    op.alter_column('word_documents', 'text_id', new_column_name='document_id')
    
    # Restore enum
    op.execute("ALTER TYPE wordtexttype RENAME TO worddocumenttype")
    
    # Drop document_id foreign key and column from texts
    op.drop_constraint('texts_document_id_fkey', 'texts', type_='foreignkey')
    op.drop_index(op.f('ix_texts_document_id'), table_name='texts')
    op.drop_column('texts', 'document_id')
    op.drop_column('texts', 'is_primary')
    op.drop_column('texts', 'title')
    
    # Drop documents table
    op.drop_table('documents')
    
    # Rename texts back to documents
    op.rename_table('texts', 'documents')

