"""
Enumerations for lexicographic fields.

Two kinds of enums live here:
- Lexeme-level: properties of the dictionary entry (POS, gender, animacy,
  register, status). One value per Lexeme.
- WordForm-level: properties of a specific inflected form (plurality, case,
  verb aspect). One value per WordForm.

When adding a value, update the corresponding Alembic migration's
`postgresql.ENUM` so the database type matches.
"""
import enum


# ---------------------------------------------------------------------------
# Lexeme-level enums
# ---------------------------------------------------------------------------


class PartOfSpeech(str, enum.Enum):
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
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"
    COMMON = "common"
    ANIMATE = "animate"
    INANIMATE = "inanimate"
    NOT_APPLICABLE = "not_applicable"


class Animacy(str, enum.Enum):
    ANIMATE = "animate"
    INANIMATE = "inanimate"
    HUMAN = "human"
    NON_HUMAN = "non_human"
    PERSONAL = "personal"
    IMPERSONAL = "impersonal"
    NOT_APPLICABLE = "not_applicable"


class Register(str, enum.Enum):
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


class LexemeStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


# Back-compat alias — old code referred to this as WordStatus.
WordStatus = LexemeStatus


# ---------------------------------------------------------------------------
# WordForm-level enums (inflection)
# ---------------------------------------------------------------------------


class Plurality(str, enum.Enum):
    SINGULAR = "singular"
    PLURAL = "plural"
    DUAL = "dual"
    TRIAL = "trial"
    PAUCAL = "paucal"
    COLLECTIVE = "collective"
    NOT_APPLICABLE = "not_applicable"


class GrammaticalCase(str, enum.Enum):
    NOMINATIVE = "nominative"
    ACCUSATIVE = "accusative"
    GENITIVE = "genitive"
    DATIVE = "dative"
    ABLATIVE = "ablative"
    LOCATIVE = "locative"
    INSTRUMENTAL = "instrumental"
    VOCATIVE = "vocative"
    PARTITIVE = "partitive"
    COMITATIVE = "comitative"
    ESSIVE = "essive"
    TRANSLATIVE = "translative"
    ERGATIVE = "ergative"
    ABSOLUTIVE = "absolutive"
    NOT_APPLICABLE = "not_applicable"
    OTHER = "other"


class VerbAspect(str, enum.Enum):
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


# ---------------------------------------------------------------------------
# Relationship-qualifier enums
# ---------------------------------------------------------------------------


class SynonymNuance(str, enum.Enum):
    """
    How tightly two lexemes overlap when linked as synonyms.
    """
    EXACT = "exact"            # full interchangeable synonym
    NEAR = "near"              # close but not interchangeable in every context
    REGISTER_VARIANT = "register_variant"  # same meaning, different register
    REGIONAL_VARIANT = "regional_variant"  # dialect/regional alternative
    HYPERNYM = "hypernym"      # the other lexeme is a broader category
    HYPONYM = "hyponym"        # the other lexeme is a narrower subtype
    OTHER = "other"


class AntonymType(str, enum.Enum):
    """
    Logical shape of an antonym pair.
    """
    GRADABLE = "gradable"          # hot/cold — admits intermediate values
    COMPLEMENTARY = "complementary"  # alive/dead — strict mutual exclusion
    CONVERSE = "converse"          # buy/sell, parent/child — relational inverse
    DIRECTIONAL = "directional"    # up/down, north/south
    OTHER = "other"
