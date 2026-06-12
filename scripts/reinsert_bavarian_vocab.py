# ruff: noqa: E501
"""
Re-insert Bavarian vocabulary after the Word→Lexeme/WordForm refactor.

Reads from a self-contained inventory below (regrouped from the 197 flat
`words` rows that the lexeme-split migration dropped), POSTs to the prod
API at https://nativo-api.fly.dev, and re-creates English↔Bavarian
translation links.

Inventory shape:

  BAR_LEXEMES: list[dict]
      Each entry is a CreateLexemeData payload. `lemma_form` carries the
      canonical surface form; `additional_forms` carry the rest of the
      paradigm (verb conjugations, plurals, etc.).

  ENG_LEXEMES: list[dict]
      Same shape, but for the English side. One row per gloss we link to.

  TRANSLATIONS: list[tuple[str, str]]
      Pairs of (BAR lemma, ENG lemma). Both must exist in the inventory
      lists above with that exact `lemma`. We use lemma + language_id as
      the lookup key when wiring the translations.

Idempotency: the script aborts if Bavarian or English lexemes already
exist in the target language (so it's safe to re-run after a fresh
migration but won't double up on a populated DB).
"""

from __future__ import annotations

import os
import sys
from typing import Any

import requests

API = os.environ.get("API_BASE", "https://nativo-api.fly.dev")
USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

BAR_ID = "051e55a2-91d3-4303-b0bf-a23b733ced75"
ENG_ID = "54266e9b-19de-4b17-9e9d-15595ce4e7af"


# ---------------------------------------------------------------------------
# Inventory — Bavarian
# ---------------------------------------------------------------------------

# Multi-form lexemes (paradigm collapses). The first 10 entries each absorb
# multiple ex-Word rows.

BAR_PARADIGMS: list[dict[str, Any]] = [
    # "to be" — sei
    {
        "lemma": "sei",
        "lemma_form": {"form": "sei", "is_lemma": True, "notes": "infinitive 'to be'"},
        "additional_forms": [
            {"form": "bin", "notes": "1sg present"},
            {"form": "bist", "notes": "2sg present"},
            {"form": "is", "notes": "3sg present"},
            {"form": "saids", "plurality": "dual", "notes": "2pl present (dual + plural)"},
            {"form": "san", "plurality": "plural", "notes": "1pl/3pl present"},
            {"form": "han", "plurality": "plural", "notes": "alt 1pl/3pl present"},
        ],
        "part_of_speech": "verb",
        "notes": "to be. Example: 'I vui aloa sei' = 'I want to be alone'.",
    },
    # "to have" — hóm
    {
        "lemma": "hóm",
        "lemma_form": {
            "form": "hóm",
            "is_lemma": True,
            "notes": "infinitive; also 1pl/3pl present",
        },
        "additional_forms": [
            {"form": "hób", "notes": "1sg present"},
            {"form": "hóst", "notes": "2sg present"},
            {"form": "hód", "notes": "3sg present"},
            {"form": "hóbds", "plurality": "dual", "notes": "2pl present (dual + plural)"},
        ],
        "part_of_speech": "verb",
        "notes": "to have.",
    },
    # "to do" — máha
    {
        "lemma": "máha",
        "lemma_form": {
            "form": "máha",
            "is_lemma": True,
            "notes": "infinitive; also 1pl/3pl present",
        },
        "additional_forms": [
            {"form": "máh", "notes": "1sg present"},
            {"form": "máhsd", "notes": "2sg present"},
            {"form": "máhd", "notes": "3sg present"},
            {"form": "máhds", "plurality": "dual", "notes": "2pl present (dual + plural)"},
        ],
        "part_of_speech": "verb",
        "notes": "to do.",
    },
    # "to see / view" — ségn
    {
        "lemma": "ségn",
        "lemma_form": {"form": "ségn", "is_lemma": True, "notes": "infinitive"},
        "additional_forms": [
            {
                "form": "sig",
                "notes": "imperative AND 1sg present. Example: 'I sig an mo' = 'I see a man'; 'sig om' = 'see above'.",
            },
        ],
        "part_of_speech": "verb",
        "notes": "to see / view.",
    },
    # "to search" — suaha
    {
        "lemma": "suaha",
        "lemma_form": {"form": "suaha", "is_lemma": True, "notes": "infinitive"},
        "additional_forms": [
            {
                "form": "suah",
                "notes": "imperative (same surface as the noun 'suah' = search — they're separate lexemes)",
            },
            {"form": "suaht", "notes": "3sg present"},
        ],
        "part_of_speech": "verb",
        "notes": "to search.",
    },
    # "to give / there is" — gém
    {
        "lemma": "gém",
        "lemma_form": {"form": "gém", "is_lemma": True, "notes": "infinitive 'to give / there is'"},
        "additional_forms": [
            {"form": "gibd", "notes": "3sg present indicative"},
        ],
        "part_of_speech": "verb",
        "notes": "to give; also 'there is/are' (es gibd).",
    },
    # "word" — voat
    {
        "lemma": "voat",
        "lemma_form": {
            "form": "voat",
            "is_lemma": True,
            "plurality": "singular",
            "grammatical_case": "nominative",
        },
        "additional_forms": [
            {
                "form": "veata",
                "plurality": "plural",
                "grammatical_case": "nominative",
                "notes": "plural",
            },
        ],
        "part_of_speech": "noun",
        "gender": "neuter",
        "notes": "word.",
    },
    # "language" — cbráh
    {
        "lemma": "cbráh",
        "lemma_form": {
            "form": "cbráh",
            "is_lemma": True,
            "plurality": "singular",
            "grammatical_case": "nominative",
        },
        "additional_forms": [
            {
                "form": "cbráha",
                "plurality": "plural",
                "grammatical_case": "nominative",
                "notes": "plural",
            },
        ],
        "part_of_speech": "noun",
        "gender": "feminine",
        "notes": "language. Core noun of the project.",
    },
    # "child" — kind
    {
        "lemma": "kind",
        "lemma_form": {
            "form": "kind",
            "is_lemma": True,
            "plurality": "singular",
            "grammatical_case": "nominative",
        },
        "additional_forms": [
            {
                "form": "kinda",
                "plurality": "plural",
                "grammatical_case": "nominative",
                "notes": "plural",
            },
        ],
        "part_of_speech": "noun",
        "gender": "neuter",
        "notes": "child.",
    },
    # "pig" — sau
    {
        "lemma": "sau",
        "lemma_form": {
            "form": "sau",
            "is_lemma": True,
            "plurality": "singular",
            "grammatical_case": "nominative",
        },
        "additional_forms": [
            {
                "form": "sai",
                "plurality": "plural",
                "grammatical_case": "nominative",
                "notes": "plural 'pigs'",
            },
        ],
        "part_of_speech": "noun",
        "gender": "feminine",
        "notes": "pig.",
    },
]


# Flat single-form lexemes — nouns
# Each tuple: (lemma, gender, notes, eng_gloss)
BAR_NOUNS = [
    # singular-only nouns
    ("bua", "masculine", "", "boy"),
    ("test", "masculine", "smoke-test entry preserved for the test page", "test"),
    ("veatabuah", "neuter", "compound veata+buah", "dictionary"),
    ("veataguad", "neuter", "compound veata+guad", "vocabulary"),
    (
        "voatsámlung",
        "feminine",
        "compound voat+sámlung. Plural voatsámlunga attested.",
        "vocabulary",
    ),
    ("buah", "neuter", "plural form biaha unverified", "book"),
    ("guad", "neuter", "also covers wealth, good", "good"),
    ("sámlung", "feminine", "plural sámlunga unverified", "collection"),
    ("dokument", "neuter", "same form used for plural in the UI", "document"),
    ("afnáma", "feminine", "same form used for plural; appears in compound tonafnáma", "recording"),
    ("tonafnáma", "feminine", "compound ton+afnáma", "audio recording"),
    ("ton", "masculine", "also serves as 'audio'", "sound"),
    ("ivasetsung", "feminine", "plural ivasetsunga attested", "translation"),
    ("ascbráh", "feminine", "plural ascbráha attested", "outgoing language"),
    ("veit", "feminine", "", "world"),
    ("eab", "neuter", "", "heritage"),
    ("afdróg", "masculine", "also: task", "assignment"),
    ("midheifa", "masculine", "same form for plural; gender-neutral by convention", "helper"),
    ("ascdeam", "neuter", "", "topic"),
    ("visn", "neuter", "", "knowledge"),
    ("minutn", "feminine", "", "minute"),
    ("iór", "neuter", "same form for plural", "year"),
    ("foatcrit", "masculine", "", "progress"),
    ("ivasiht", "feminine", "", "overview"),
    ("blátfoam", "feminine", "loanword", "platform"),
    ("meni", "neuter", "loanword", "menu"),
    ("profil", "neuter", "loanword", "profile"),
    ("nutsa", "masculine", "same form for plural", "user"),
    ("kentnis", "feminine", "", "fluency"),
    ("tréfa", "masculine", "also: hit. Same form for plural.", "result"),
    ("duan", "neuter", "verbal noun", "action"),
    ("adminblóds", "masculine", "compound admin+blóds", "admin panel"),
    ("generaradsiona", "feminine", "loanword, plural", "generations"),
    ("suah", "feminine", "also imperative of suaha", "search"),
    ("dsuicbráh", "feminine", "compound dsui+cbráh", "target language"),
    (
        "bedincbráh",
        "feminine",
        "compound: stem of bedina (to control) + cbráh",
        "interface language",
    ),
    ("mo", "masculine", "'Da mo' = 'the man'; 'Dea mo' = 'that man'.", "man"),
    ("muada", "feminine", "component of muadacbráhla", "mother"),
    ("cbráhla", "masculine", "agent form derived from cbráh; component of muadacbráhla", "speaker"),
    ("dsui", "neuter", "component of dsuicbráh; also: goal", "target"),
    ("blóds", "masculine", "component of adminblóds; also: place, panel", "panel"),
    ("kean", "masculine", "component of keanveata", "core"),
    ("muadacbráhla", "masculine", "compound muada+cbráhla; same form for plural", "native speaker"),
    ("bitn", "feminine", "singular and plural use the same form", "request"),
    ("frau", "feminine", "", "woman"),
    ("hund", "masculine", "", "dog"),
    ("dic", "masculine", "", "table"),
    ("sesl", "masculine", "", "chair"),
    ("haus", "neuter", "", "house"),
]

# Plural-marked standalone nouns (no singular form attested standalone)
BAR_NOUNS_PLURAL = [
    ("keanveata", "neuter", "compound kean+veata", "key words"),
]


# Flat single-form lexemes — verbs (separable / derived; conjugation unverified)
BAR_VERBS = [
    ("festhóitn", "to hold fast, to record", "record"),
    ("eahóitn", "to preserve", "preserve"),
    ("dahóitn", "to keep", "keep"),
    ("rétn", "to rescue", "rescue"),
    ("ocaugn", "in a reference", "see"),
    ("nema", "combines with prefixes", "take"),
    ("afnema", "audio; to take down", "record"),
    ("baidrógn", "separable: dróg ... bai", "contribute"),
    ("datsuafign", "formal alternative", "add"),
    ("dadsuagém", "in 'add' contexts", "add"),
    ("ivasetsn", "", "translate"),
    ("houhlón", "", "upload"),
    ("afbaun", "to establish", "build"),
    ("cbaihan", "to save data", "save"),
    ("tailn", "", "share"),
    ("omein", "to log in", "log in"),
    ("óbmein", "to log out", "log out"),
    ("registrian", "to sign up; imperative Registria", "sign up"),
    ("dsoagn", "reflexive dsoagn si = to appear", "show"),
    ("eigém", "to input", "enter"),
    ("dróg", "combines with bai → baidrógn", "carry"),
    ("fasuaha", "imperative fasuah's", "try"),
    ("baun", "3rd pl form same as infinitive", "build"),
    ("lón", "present lót", "let"),
    ("umcaugn", "to look around", "explore"),
    ("midmáha", "user-corrected from earlier midmáhn; past participle midgmáhd", "participate"),
    ("klasifidsian", "3sg klasifidsiad", "classify"),
    ("dadsuaduan", "3sg dadsuaduad", "add"),
    ("bedina", "verb whose stem appears in compound bedincbráh", "operate"),
]


# Adjectives (past participles treated as distinct lexemes)
BAR_ADJECTIVES = [
    ("digitale", "loanword", "digital"),
    ("bedrotn", "", "endangered"),
    ("gcrimne", "past participle as adjective", "written"),
    ("dahóitne", "past participle of dahóitn", "preserved"),
    ("dokumentiade", "past participle", "documented"),
    ("umfángraihe", "", "comprehensive"),
    ("ehde", "also: authentic", "authentic"),
    ("letsde", "also: last", "latest"),
    ("easte", "", "first"),
    ("cbráhlihs", "relating to language", "linguistic"),
    ("kemade", "also: future. Present participle.", "coming"),
    ("gcétsd", "past participle", "endangered"),
    ("fabundn", "past participle; declined fabundne", "connected"),
    ("feigclógn", "past participle", "suggested"),
    ("midgmáhd", "past participle of midmáha", "participated"),
    ("meara", "comparative", "more"),
]


# Adverbs
BAR_ADVERBS = [
    ("ned", "negation", "not"),
    ("bóid", "", "soon"),
    ("numoi", "", "again"),
    ("nima", "", "no more"),
    ("no", "", "still"),
    ("ruiga", "", "calmly"),
    ("co", "", "already"),
    ("dó", "", "there"),
    ("óis", "", "all"),
    ("om", "", "above"),
    ("réhds", "", "right"),
]


# Pronouns — including the homograph splits
# Each entry: (lemma, notes, eng_gloss). For homographs we add a sense
# discriminator to the notes so the two `si`/`es`/`de` rows are distinct.
BAR_PRONOUNS = [
    ("mia", "1pl subject pronoun", "we"),
    ("ma", "indefinite 'one'", "one"),
    ("di", "2sg object pronoun", "you"),
    ("si", "reflexive pronoun", "oneself"),
    ("ole", "", "all"),
    ("oans", "indefinite 'someone'", "someone"),
    ("niks", "", "nothing"),
    ("vo", "", "what"),
    ("i", "1sg subject pronoun; written 'I' sentence-initial", "I"),
    ("du", "2sg subject pronoun", "you"),
    ("ea", "3sg masculine subject pronoun", "he"),
]

# Pronoun homographs — same surface form, different lexeme. We embed a
# discriminator in `notes` so each lexeme is clearly distinguished, and
# the English glosses below are matched 1:1.
BAR_PRONOUN_HOMOGRAPHS = [
    {"lemma": "es", "notes": "3sg neuter subject pronoun 'it'", "eng": "it"},
    {"lemma": "es", "notes": "2nd-person DUAL subject pronoun 'you two'", "eng": "you two"},
    {"lemma": "si", "notes": "3sg feminine subject pronoun 'she'", "eng": "she"},
    {"lemma": "de", "notes": "3pl subject pronoun 'they'", "eng": "they"},
    {"lemma": "ia", "notes": "2nd-person PLURAL subject pronoun 'you all'", "eng": "you all"},
    {
        "lemma": "dea",
        "notes": "demonstrative / relative pronoun 'that one'. 'Dea mo' = 'that man'.",
        "eng": "that one",
    },
    {
        "lemma": "se",
        "notes": "formal/polite 'you'; same verb conjugation as 3pl 'de'",
        "eng": "you (formal)",
    },
    {
        "lemma": "den",
        "notes": "demonstrative pronoun 'that' (m sg). 'Den mo' = 'that man'.",
        "eng": "that",
    },
    {
        "lemma": "dene",
        "notes": "demonstrative pronoun 'these / those' (pl, all genders). 'I gib's dene kinda' = 'I give it to these children'.",
        "eng": "these",
    },
]


# Determiners — including the article homograph splits
BAR_DETERMINERS = [
    ("oana", "feminine 'a / one'", "a"),
    ("a", "indefinite article (m/n nom; f nom)", "a"),
    ("koa", "negation 'no' (nom, all genders)", "no"),
    ("koane", "negation 'no' (plural)", "no"),
    ("da", "definite article 'the' (m sg nom)", "the"),
    ("de", "definite article 'the' (pl nom; same surface as 3pl pronoun — separate lexeme)", "the"),
    ("dera", "definite article 'the' (f sg gen/dat in some uses)", "the"),
    ("dem", "definite article 'the' (m/n sg dat)", "the"),
    ("s'", "definite article 'the' (n sg nom)", "the"),
    ("d'", "definite article 'the' (f sg nom)", "the"),
    ("des", "demonstrative determiner 'this/that'", "this"),
]

# Article/numeral homograph splits (multi-attribute)
BAR_ARTICLE_PARADIGM = [
    {
        "lemma": "'n",
        "lemma_form": {
            "form": "'n",
            "is_lemma": True,
            "grammatical_case": "accusative",
            "plurality": "singular",
        },
        "pos": "determiner",
        "gender": "masculine",
        "notes": "Definite article 'the' (m sg acc). NOT a contraction of 'an'. Example: 'I sig 'n mo' = 'I see the man'.",
        "eng": "the",
    },
    {
        "lemma": "an",
        "lemma_form": {
            "form": "an",
            "is_lemma": True,
            "grammatical_case": "accusative",
            "plurality": "singular",
        },
        "pos": "determiner",
        "gender": "masculine",
        "notes": "Indefinite article 'a' (m sg acc; also covers n sg dat indef). 'I sig an mo' = 'I see a man'; 'I gib an kind a buah' = 'I give a child a book'.",
        "eng": "a",
    },
    {
        "lemma": "koam",
        "lemma_form": {
            "form": "koam",
            "is_lemma": True,
            "grammatical_case": "dative",
            "plurality": "singular",
        },
        "pos": "determiner",
        "gender": "masculine",
        "notes": "Negation 'no' (m/n sg dat). 'I gib koam kind a buah' = 'I give no child a book'.",
        "eng": "no",
    },
    {
        "lemma": "koana",
        "lemma_form": {
            "form": "koana",
            "is_lemma": True,
            "grammatical_case": "dative",
            "plurality": "singular",
        },
        "pos": "determiner",
        "gender": "feminine",
        "notes": "Negation 'no' (f sg dat). 'I gib koana frau a buah' = 'I give no woman a book'.",
        "eng": "no",
    },
    {
        "lemma": "oa",
        "lemma_form": {
            "form": "oa",
            "is_lemma": True,
            "grammatical_case": "nominative",
            "plurality": "singular",
        },
        "pos": "numeral",
        "gender": None,
        "notes": "Cardinal numeral 'one' (m/n/f sg counting). 'Oa buah' = 'one book'.",
        "eng": "one",
    },
]


# Prepositions (all flat — including the contractions, kept as distinct
# lexemes per user decision)
BAR_PREPS = [
    ("foa", "", "for / before"),
    ("af", "", "on"),
    ("in", "", "in"),
    ("bai", "", "by / at"),
    ("mid", "", "with"),
    ("fo", "", "from / of"),
    ("fia", "", "for"),
    ("duah", "", "through"),
    ("iva", "", "over / about"),
    ("dsu", "", "to"),
    ("tsua", "", "to (alt)"),
    ("dsum", "contraction of dsu + dem", "to the"),
    ("um", "", "around / for"),
    ("aus'm", "contraction of aus + dem", "from the"),
    (
        "af'm",
        "contraction of af + dem. S' buah is af'm dic = 'the book is on the table'.",
        "on the",
    ),
    (
        "im",
        "contraction of in + dem. Written as one word. 'I bin im haus' = 'I'm in the house'.",
        "in the",
    ),
    ("mid'm", "contraction of mid + dem. 'I kim mid'm mo' = 'I come with the man'.", "with the"),
    ("fia'n", "contraction of fia + an. 'I máh's fia'n mo' = 'I do it for the man'.", "for the"),
    (
        "fom",
        "contraction of fo + dem. Written as one word. 'S' buah fom mo' = 'the book of the man'.",
        "of the",
    ),
]


# Conjunctions, particles, numerals
BAR_CONJS = [
    ("und", "", "and"),
    ("oda", "", "or"),
    ("ven", "", "when / if"),
]

BAR_PARTICLES = [
    ("bitce", "", "please"),
]

BAR_NUMERALS_FLAT = [
    ("dausnd", "", "thousand"),
]


# ---------------------------------------------------------------------------
# Helper: build the full lexeme list to POST
# ---------------------------------------------------------------------------


def build_bar_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []

    # Paradigms first (multi-form lexemes).
    for p in BAR_PARADIGMS:
        payloads.append({"language_id": BAR_ID, **p})

    # Flat singular nouns
    for lemma, gender, notes, _eng in BAR_NOUNS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {
                    "form": lemma,
                    "is_lemma": True,
                    "plurality": "singular",
                    "grammatical_case": "nominative",
                },
                "part_of_speech": "noun",
                "gender": gender,
                "notes": notes,
            }
        )
    # Plural-only nouns
    for lemma, gender, notes, _eng in BAR_NOUNS_PLURAL:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {
                    "form": lemma,
                    "is_lemma": True,
                    "plurality": "plural",
                    "grammatical_case": "nominative",
                },
                "part_of_speech": "noun",
                "gender": gender,
                "notes": notes,
            }
        )

    # Flat verbs
    for lemma, notes, _eng in BAR_VERBS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True, "verb_aspect": "imperfective"},
                "part_of_speech": "verb",
                "notes": notes,
            }
        )

    # Adjectives
    for lemma, notes, _eng in BAR_ADJECTIVES:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "adjective",
                "notes": notes,
            }
        )

    # Adverbs
    for lemma, notes, _eng in BAR_ADVERBS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "adverb",
                "notes": notes,
            }
        )

    # Pronouns
    for lemma, notes, _eng in BAR_PRONOUNS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "pronoun",
                "notes": notes,
            }
        )

    # Pronoun homographs
    for entry in BAR_PRONOUN_HOMOGRAPHS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": entry["lemma"],
                "lemma_form": {"form": entry["lemma"], "is_lemma": True},
                "part_of_speech": "pronoun",
                "notes": entry["notes"],
            }
        )

    # Determiners
    for lemma, notes, _eng in BAR_DETERMINERS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "determiner",
                "notes": notes,
            }
        )

    # Article paradigm homographs
    for entry in BAR_ARTICLE_PARADIGM:
        body: dict[str, Any] = {
            "language_id": BAR_ID,
            "lemma": entry["lemma"],
            "lemma_form": entry["lemma_form"],
            "part_of_speech": entry["pos"],
            "notes": entry["notes"],
        }
        if entry["gender"]:
            body["gender"] = entry["gender"]
        payloads.append(body)

    # Prepositions
    for lemma, notes, _eng in BAR_PREPS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "preposition",
                "notes": notes,
            }
        )

    # Conjunctions
    for lemma, notes, _eng in BAR_CONJS:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "conjunction",
                "notes": notes,
            }
        )

    # Particles
    for lemma, notes, _eng in BAR_PARTICLES:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "particle",
                "notes": notes,
            }
        )

    # Numerals (flat)
    for lemma, notes, _eng in BAR_NUMERALS_FLAT:
        payloads.append(
            {
                "language_id": BAR_ID,
                "lemma": lemma,
                "lemma_form": {"form": lemma, "is_lemma": True},
                "part_of_speech": "numeral",
                "notes": notes,
            }
        )

    return payloads


def collect_eng_glosses() -> list[tuple[str, str]]:
    """Returns list of (lemma, pos) for all English entries needed for translations."""
    out: list[tuple[str, str]] = []

    # Paradigm meanings
    out.extend(
        [
            ("to be", "verb"),
            ("to have", "verb"),
            ("to do", "verb"),
            ("to see", "verb"),
            ("to search", "verb"),
            ("to give", "verb"),
            ("word", "noun"),
            ("language", "noun"),
            ("child", "noun"),
            ("pig", "noun"),
        ]
    )

    for _, _, _, eng in BAR_NOUNS:
        out.append((eng, "noun"))
    for _, _, _, eng in BAR_NOUNS_PLURAL:
        out.append((eng, "noun"))
    for _, _, eng in BAR_VERBS:
        out.append((eng, "verb"))
    for _, _, eng in BAR_ADJECTIVES:
        out.append((eng, "adjective"))
    for _, _, eng in BAR_ADVERBS:
        out.append((eng, "adverb"))
    for _, _, eng in BAR_PRONOUNS:
        out.append((eng, "pronoun"))
    for entry in BAR_PRONOUN_HOMOGRAPHS:
        out.append((entry["eng"], "pronoun"))
    for _, _, eng in BAR_DETERMINERS:
        out.append((eng, "determiner"))
    for entry in BAR_ARTICLE_PARADIGM:
        out.append((entry["eng"], entry["pos"]))
    for _, _, eng in BAR_PREPS:
        out.append((eng, "preposition"))
    for _, _, eng in BAR_CONJS:
        out.append((eng, "conjunction"))
    for _, _, eng in BAR_PARTICLES:
        out.append((eng, "particle"))
    for _, _, eng in BAR_NUMERALS_FLAT:
        out.append((eng, "numeral"))

    # Dedupe preserving order
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for lemma, pos in out:
        key = (lemma, pos)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((lemma, pos))
    return deduped


def build_eng_payloads(glosses: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "language_id": ENG_ID,
            "lemma": lemma,
            "lemma_form": {"form": lemma, "is_lemma": True},
            "part_of_speech": pos,
        }
        for lemma, pos in glosses
    ]


def build_translation_pairs() -> list[tuple[str, str]]:
    """Returns list of (BAR lemma sense-key, ENG lemma) pairs.

    For Bavarian homographs we use the discriminator from the notes
    field; for the API we look up by lemma + (lazy) first-match. To
    avoid ambiguity we instead use the per-entry inserted ID — see
    `wire_translations` below.
    """
    # Built by index: we iterate the bar payloads and ENG glosses in
    # the same order they were inserted; the pairing is positional.
    raise NotImplementedError  # see wire_translations


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def login() -> str:
    r = requests.post(
        f"{API}/api/v1/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def existing_count(token: str, language_id: str) -> int:
    r = requests.get(
        f"{API}/api/v1/words/",
        params={"language_id": language_id, "include_all_statuses": True, "limit": 1000},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    r.raise_for_status()
    return len(r.json())


def post_lexeme(token: str, payload: dict[str, Any]) -> str:
    r = requests.post(
        f"{API}/api/v1/words/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if r.status_code >= 400:
        raise SystemExit(f"POST failed for {payload['lemma']!r}: {r.status_code} {r.text[:300]}")
    return r.json()["id"]


def post_translation(token: str, bar_id: str, eng_id: str) -> None:
    r = requests.post(
        f"{API}/api/v1/words/{bar_id}/translations",
        json={"other_lexeme_id": eng_id},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    if r.status_code >= 400 and r.status_code != 409:
        raise SystemExit(
            f"Translation link failed bar={bar_id} eng={eng_id}: {r.status_code} {r.text[:300]}"
        )


def main() -> int:
    print("Logging in...")
    token = login()

    bar_existing = existing_count(token, BAR_ID)
    eng_existing = existing_count(token, ENG_ID)
    if bar_existing or eng_existing:
        print(
            f"ABORT: target DB already has {bar_existing} BAR / {eng_existing} ENG lexemes. Re-insert is only safe against an empty DB."
        )
        return 1

    bar_payloads = build_bar_payloads()
    eng_glosses = collect_eng_glosses()
    eng_payloads = build_eng_payloads(eng_glosses)

    # Build the lookup (bar_index -> eng_lemma) in inventory order.
    # For each bar entry we know what English gloss it points at: it's
    # the corresponding entry in the same source list.

    print(f"Will insert {len(bar_payloads)} BAR lexemes and {len(eng_payloads)} ENG lexemes.")

    print("--- Inserting Bavarian lexemes ---")
    bar_ids: list[str] = []
    for i, payload in enumerate(bar_payloads, 1):
        bid = post_lexeme(token, payload)
        bar_ids.append(bid)
        if i % 10 == 0 or i == len(bar_payloads):
            print(f"  {i}/{len(bar_payloads)} {payload['lemma']!r}")

    print("--- Inserting English lexemes ---")
    eng_ids: dict[tuple[str, str], str] = {}
    for i, payload in enumerate(eng_payloads, 1):
        eid = post_lexeme(token, payload)
        eng_ids[(payload["lemma"], payload["part_of_speech"])] = eid
        if i % 10 == 0 or i == len(eng_payloads):
            print(f"  {i}/{len(eng_payloads)} {payload['lemma']!r}")

    # Wire translations: walk the same inventory in the same order and
    # link each bar_ids[i] -> the matching eng entry.
    print("--- Linking translations ---")
    pairs = compute_translation_pairs()
    if len(pairs) != len(bar_ids):
        raise SystemExit(f"Pair count {len(pairs)} != BAR count {len(bar_ids)}")
    for i, (bar_idx, eng_key) in enumerate(pairs, 1):
        eid = eng_ids.get(eng_key)
        if eid is None:
            raise SystemExit(f"Missing English gloss for {eng_key!r}")
        post_translation(token, bar_ids[bar_idx], eid)
        if i % 20 == 0 or i == len(pairs):
            print(f"  {i}/{len(pairs)}")

    print("Done.")
    return 0


def compute_translation_pairs() -> list[tuple[int, tuple[str, str]]]:
    """Returns list of (bar_index, (eng_lemma, eng_pos)) in insertion order."""
    pairs: list[tuple[int, tuple[str, str]]] = []
    i = 0

    # Paradigms
    paradigm_glosses = [
        ("to be", "verb"),
        ("to have", "verb"),
        ("to do", "verb"),
        ("to see", "verb"),
        ("to search", "verb"),
        ("to give", "verb"),
        ("word", "noun"),
        ("language", "noun"),
        ("child", "noun"),
        ("pig", "noun"),
    ]
    for gloss in paradigm_glosses:
        pairs.append((i, gloss))
        i += 1

    for _, _, _, eng in BAR_NOUNS:
        pairs.append((i, (eng, "noun")))
        i += 1
    for _, _, _, eng in BAR_NOUNS_PLURAL:
        pairs.append((i, (eng, "noun")))
        i += 1
    for _, _, eng in BAR_VERBS:
        pairs.append((i, (eng, "verb")))
        i += 1
    for _, _, eng in BAR_ADJECTIVES:
        pairs.append((i, (eng, "adjective")))
        i += 1
    for _, _, eng in BAR_ADVERBS:
        pairs.append((i, (eng, "adverb")))
        i += 1
    for _, _, eng in BAR_PRONOUNS:
        pairs.append((i, (eng, "pronoun")))
        i += 1
    for entry in BAR_PRONOUN_HOMOGRAPHS:
        pairs.append((i, (entry["eng"], "pronoun")))
        i += 1
    for _, _, eng in BAR_DETERMINERS:
        pairs.append((i, (eng, "determiner")))
        i += 1
    for entry in BAR_ARTICLE_PARADIGM:
        pairs.append((i, (entry["eng"], entry["pos"])))
        i += 1
    for _, _, eng in BAR_PREPS:
        pairs.append((i, (eng, "preposition")))
        i += 1
    for _, _, eng in BAR_CONJS:
        pairs.append((i, (eng, "conjunction")))
        i += 1
    for _, _, eng in BAR_PARTICLES:
        pairs.append((i, (eng, "particle")))
        i += 1
    for _, _, eng in BAR_NUMERALS_FLAT:
        pairs.append((i, (eng, "numeral")))
        i += 1

    return pairs


if __name__ == "__main__":
    sys.exit(main())
