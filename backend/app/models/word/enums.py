"""
Enumerations for linguistic and word-related fields.
"""
import enum


class PartOfSpeech(str, enum.Enum):
    """Parts of speech"""
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


class GrammaticalCase(str, enum.Enum):
    """Grammatical case system"""
    # Core cases
    NOMINATIVE = "nominative"
    ACCUSATIVE = "accusative"
    GENITIVE = "genitive"
    DATIVE = "dative"
    
    # Additional common cases
    ABLATIVE = "ablative"
    LOCATIVE = "locative"
    INSTRUMENTAL = "instrumental"
    VOCATIVE = "vocative"
    
    # Additional cases found in various languages
    PARTITIVE = "partitive"
    COMITATIVE = "comitative"
    ESSIVE = "essive"
    TRANSLATIVE = "translative"
    ERGATIVE = "ergative"
    ABSOLUTIVE = "absolutive"
    
    # Meta
    NOT_APPLICABLE = "not_applicable"
    OTHER = "other"


class VerbAspect(str, enum.Enum):
    """Verbal aspect categories"""
    PERFECTIVE = "perfective"
    IMPERFECTIVE = "imperfective"
    PROGRESSIVE = "progressive"
    CONTINUOUS = "continuous"
    HABITUAL = "habitual"
    ITERATIVE = "iterative"
    INCHOATIVE = "inchoative"
    PERFECT = "perfect"
    PROSPECTIVE = "prospective"
    NOT_APPLICABLE = "not_applicable"
    OTHER = "other"


class Animacy(str, enum.Enum):
    """Animacy distinction"""
    ANIMATE = "animate"
    INANIMATE = "inanimate"
    HUMAN = "human"
    NON_HUMAN = "non_human"
    PERSONAL = "personal"
    IMPERSONAL = "impersonal"
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


class WordStatus(str, enum.Enum):
    """Publication status of word entries"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

