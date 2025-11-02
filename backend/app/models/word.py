from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class PartOfSpeech(str, enum.Enum):
    """Enumeration of parts of speech"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    ARTICLE = "article"
    DETERMINER = "determiner"
    PARTICLE = "particle"
    NUMERAL = "numeral"
    CLASSIFIER = "classifier"
    OTHER = "other"


class GrammaticalGender(str, enum.Enum):
    """Grammatical gender categories"""
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"
    COMMON = "common"
    ANIMATE = "animate"
    INANIMATE = "inanimate"
    NOT_APPLICABLE = "not_applicable"


class Plurality(str, enum.Enum):
    """Number categories"""
    SINGULAR = "singular"
    PLURAL = "plural"
    DUAL = "dual"
    TRIAL = "trial"
    PAUCAL = "paucal"
    COLLECTIVE = "collective"
    NOT_APPLICABLE = "not_applicable"


class Register(str, enum.Enum):
    """Language register/formality levels"""
    FORMAL = "formal"
    INFORMAL = "informal"
    COLLOQUIAL = "colloquial"
    SLANG = "slang"
    CEREMONIAL = "ceremonial"
    ARCHAIC = "archaic"
    TABOO = "taboo"
    POETIC = "poetic"
    TECHNICAL = "technical"
    NEUTRAL = "neutral"


class DifficultyLevel(str, enum.Enum):
    """Learning difficulty levels"""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    NATIVE = "native"


class WordStatus(str, enum.Enum):
    """Publication status of word entries"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Word(Base):
    """
    Comprehensive word model for endangered language preservation.
    
    This model captures linguistic, cultural, and educational aspects of words
    to provide a rich resource for language preservation and learning.
    """
    __tablename__ = "words"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Core Word Information
    word = Column(String(255), nullable=False, index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False, index=True)
    romanization = Column(String(255), nullable=True, index=True)  # For non-Latin scripts
    ipa_pronunciation = Column(String(255), nullable=True)  # International Phonetic Alphabet

    # Linguistic Information
    part_of_speech = Column(SQLEnum(PartOfSpeech), nullable=True, index=True)
    gender = Column(SQLEnum(GrammaticalGender), nullable=True)
    plurality = Column(SQLEnum(Plurality), nullable=True)
    grammatical_case = Column(String(50), nullable=True)  # Nominative, accusative, etc.
    verb_aspect = Column(String(50), nullable=True)  # Perfective, imperfective, etc.
    animacy = Column(String(50), nullable=True)  # Animate/inanimate distinction
    
    # Meaning & Context
    definition = Column(Text, nullable=False)  # Primary definition
    literal_translation = Column(Text, nullable=True)  # Word-for-word meaning
    context_notes = Column(Text, nullable=True)  # Cultural or contextual information
    usage_examples = Column(Text, nullable=True)  # JSON array of example sentences
    synonyms = Column(Text, nullable=True)  # JSON array of synonym IDs or words
    antonyms = Column(Text, nullable=True)  # JSON array of antonym IDs or words
    related_words = Column(Text, nullable=True)  # JSON array of related word IDs
    
    # Audio & Media
    audio_id = Column(Integer, ForeignKey("audio.id"), nullable=True)  # Primary pronunciation
    image_url = Column(String(500), nullable=True)  # Visual reference
    
    # Etymology & Cultural Context
    etymology = Column(Text, nullable=True)  # Origin and historical development
    cultural_significance = Column(Text, nullable=True)  # Cultural importance
    register = Column(SQLEnum(Register), nullable=True, default=Register.NEUTRAL)
    regional_variant = Column(String(255), nullable=True)  # Dialect information
    
    # Learning & Classification
    difficulty_level = Column(SQLEnum(DifficultyLevel), nullable=True, index=True)
    frequency_rank = Column(Integer, nullable=True)  # Usage frequency (1 = most common)
    category = Column(String(100), nullable=True, index=True)  # Domain: nature, family, food, etc.
    tags = Column(Text, nullable=True)  # JSON array of additional tags
    is_endangered_specific = Column(Boolean, default=False)  # Unique to this endangered language
    
    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_verified = Column(Boolean, default=False, index=True)
    status = Column(SQLEnum(WordStatus), default=WordStatus.DRAFT, index=True)
    source = Column(String(500), nullable=True)  # Source of documentation
    notes = Column(Text, nullable=True)  # Additional notes for internal use
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="words")
    audio = relationship("Audio", foreign_keys=[audio_id])
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="words_created")
    verified_by = relationship("User", foreign_keys=[verified_by_id], back_populates="words_verified")
    
    def __repr__(self):
        return f"<Word(id={self.id}, word='{self.word}', language_id={self.language_id}, status={self.status})>"
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True

