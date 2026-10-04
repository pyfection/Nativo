import uuid
from datetime import UTC, datetime

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.database import Base  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.word import Lexeme, LexemeStatus, WordForm  # noqa: E402
from app.services import transcription_service  # noqa: E402
from app.utils import phoneme_recognizer  # noqa: E402
from app.utils.ipa import segments, spell_segments, sub_cost  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def language(db_session) -> Language:
    now = _now()
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="test-user",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
        created_at=now,
        updated_at=now,
    )
    language = Language(
        id=uuid.uuid4(),
        name="Bavarian",
        native_name="Boarisch",
        iso_639_3="bar",
        managed=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([user, language])
    db_session.flush()
    language.test_user = user
    return language


def _seed(
    session: Session,
    language: Language,
    form: str,
    ipa: str | None,
    status: LexemeStatus = LexemeStatus.PUBLISHED,
) -> WordForm:
    now = _now()
    lexeme = Lexeme(
        id=uuid.uuid4(),
        language_id=language.id,
        lemma=form,
        created_by_id=language.test_user.id,
        status=status,
        created_at=now,
        updated_at=now,
    )
    session.add(lexeme)
    session.flush()
    word_form = WordForm(
        id=uuid.uuid4(),
        lexeme_id=lexeme.id,
        form=form,
        ipa_pronunciation=ipa,
        is_lemma=True,
        created_at=now,
        updated_at=now,
    )
    session.add(word_form)
    session.flush()
    return word_form


# ---------------------------------------------------------------------------
# IPA utilities
# ---------------------------------------------------------------------------


def test_segments_drop_stress_length_diacritics_and_spaces():
    assert segments("/ˈʃeː/") == ("ʃ", "e")
    assert segments("ɡɛɐ̯n") == segments("g ɛ ɐ n")
    assert segments("b̥ɪç") == ("b", "ɪ", "ç")
    assert segments("ɡɔt, i!") == ("ɡ", "ɔ", "t", "i")
    assert segments("haɪ t ts uː") == ("h", "a", "ɪ", "t", "s", "u")  # doubled t is one


def test_sub_cost_prefers_near_misses():
    assert sub_cost("b", "p") < sub_cost("b", "s") < sub_cost("b", "a")
    assert sub_cost("e", "ɛ") < sub_cost("e", "u")


def test_spell_segments_uses_the_agreed_letters():
    assert spell_segments(segments("ˈʃbrɐha")) == "cbráha"
    assert spell_segments(segments("voat")) == "voat"
    assert spell_segments(segments("dsruk")) == "dsruk"
    assert spell_segments(segments("tsvoa")) == "tsvoa"
    assert spell_segments(segments("tʃɛɔ")) == "tcéó"
    assert spell_segments(segments("iɐ")) == "iá"  # vowel pairs aren't special
    assert spell_segments(segments("ʃɑŋk")) == "cánk"


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------


def test_segments_unbroken_ipa_into_lexicon_words(db_session, language):
    for form, ipa in [("mia", "miɐ"), ("san", "san"), ("heid", "haɪd"), ("dahoam", "daˈhɔɐ̯m")]:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, "miɐsanhaɪtdahɔɐm")

    assert result.text == "Mia san heid dahoam"
    assert all(t.known for t in result.tokens)
    assert result.lexicon_size == 4


def test_near_miss_still_matches_with_lower_confidence(db_session, language):
    _seed(db_session, language, "hob", "hɔb")

    result = transcription_service.transcribe_ipa(db_session, language.id, "hɔp")

    (token,) = result.tokens
    assert token.spelling == "Hob"  # first word is capitalised
    assert 0 < token.confidence < 1
    assert token.candidates[0].distance > 0


def test_unknown_stretch_falls_back_to_spelling_rules(db_session, language):
    _seed(db_session, language, "i", "i")

    result = transcription_service.transcribe_ipa(db_session, language.id, "i ʃtoɐ")

    assert [t.spelling for t in result.tokens] == ["I", "ctoá"]
    assert [t.known for t in result.tokens] == [True, False]


def test_homophones_with_same_spelling_are_not_ambiguous(db_session, language):
    # "san" (are) and "san" (to sow) — separate lexemes, one spelling.
    _seed(db_session, language, "san", "san")
    _seed(db_session, language, "san", "saːn")

    (token,) = transcription_service.transcribe_ipa(db_session, language.id, "san").tokens

    assert len(token.candidates) == 2
    assert token.ambiguous is False


def test_different_spellings_for_same_sound_are_ambiguous(db_session, language):
    _seed(db_session, language, "Moa", "mɔɐ")
    _seed(db_session, language, "Mohr", "mɔɐ")

    (token,) = transcription_service.transcribe_ipa(db_session, language.id, "mɔɐ").tokens

    assert token.ambiguous is True
    assert {c.form for c in token.candidates} == {"Moa", "Mohr"}


def test_accent_only_spelling_difference_is_ambiguous(db_session, language):
    _seed(db_session, language, "ia", "iɐ")
    _seed(db_session, language, "iá", "iɐ")

    (token,) = transcription_service.transcribe_ipa(db_session, language.id, "iɐ").tokens

    assert token.ambiguous is True


def test_ipa_alternatives_and_unpublished_forms(db_session, language):
    _seed(db_session, language, "ned", "nɛd, nɛt")
    _seed(db_session, language, "draft", "nɛt", status=LexemeStatus.DRAFT)
    _seed(db_session, language, "noipa", None)

    (token,) = transcription_service.transcribe_ipa(db_session, language.id, "nɛt").tokens

    assert [c.form for c in token.candidates] == ["ned"]
    assert token.candidates[0].distance == 0


def test_empty_lexicon_spells_everything_by_rule(db_session, language):
    result = transcription_service.transcribe_ipa(db_session, language.id, "ʃeː")

    assert result.text == "Ce"
    assert result.lexicon_size == 0


def test_audio_path_feeds_recogniser_output_through_matcher(db_session, language, monkeypatch):
    _seed(db_session, language, "schee", "ʃeː")
    monkeypatch.setattr(phoneme_recognizer, "recognize", lambda audio: "ʃ e")

    result = transcription_service.transcribe_audio(db_session, language.id, b"fake")

    assert result.ipa == "ʃ e"
    assert result.text == "Schee"


def test_only_first_word_and_names_are_capitalised(db_session, language):
    _seed(db_session, language, "da", "da")
    _seed(db_session, language, "Sepp", "sɛp")
    _seed(db_session, language, "voat", "voat")
    _seed(db_session, language, "s'easte", "seɐste")

    result = transcription_service.transcribe_ipa(db_session, language.id, "seɐste voat da sɛp")

    assert result.text == "S'easte voat da Sepp"


# ---------------------------------------------------------------------------
# Real recordings (Lingua Libre, speaker from Niederbayern), checked by a
# native speaker. The IPA strings are the zero-shot recogniser's actual output.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("recognised", "spelling"),
    [("iː z", "is"), ("a n a m", "anam")],
)
def test_real_recordings_spelled_by_rule(recognised, spelling):
    assert spell_segments(segments(recognised)) == spelling


def test_real_recording_finds_dictionary_word_despite_noisy_ipa(db_session, language):
    # Spoken "tsvoaraloa"; the recogniser merged oa → oː and dropped the end.
    _seed(db_session, language, "tsvoaraloa", "tsvoaraloa")

    result = transcription_service.transcribe_ipa(db_session, language.id, "ts b oː r a n uː")

    assert result.text == "Tsvoaraloa"


def test_real_sentence_recording_from_native_speaker(db_session, language):
    # Recorded by a native (Central Bavarian) speaker on a phone. Dictionary
    # IPA is written letter for letter from the standard spelling.
    for form, ipa in [
        ("haid", "haid"),
        ("is", "is"),
        ("so", "so"),
        ("a", "a"),
        ("céna", "ʃɛna"),
        ("dóg", "dɔg"),
    ]:
        _seed(db_session, language, form, ipa)

    # The recogniser's actual output: d heard as r, i as e, and the final
    # g as k (word-final g/k are near-impossible to tell apart).
    recognised = "h aɪ r e s s oː a ʃ eː n a d o k"
    result = transcription_service.transcribe_ipa(db_session, language.id, recognised)

    assert result.text == "Haid is so a céna dóg"


def test_second_real_sentence_recording(db_session, language):
    for form, ipa in [
        ("i", "i"),
        ("bák", "bɐk"),
        ("an", "an"),
        ("kuaha", "kuaha"),
        ("haid", "haid"),
    ]:
        _seed(db_session, language, form, ipa)

    # Recogniser output: unvoiced Bavarian b heard as p, "ua" merged into a
    # long uː, and the final a heard as ʌ (which we fold into a).
    recognised = "iː p ɑ k a n k uː h ʌ h aɪ d"
    result = transcription_service.transcribe_ipa(db_session, language.id, recognised)

    assert result.text == "I bák an kuaha haid"


DAHOAM_RECOGNISED = "ɪ s ɪ s oː ʃ eː d ʌ v h a m"  # "Es is so ce dahoam"
DAHOAM_WORDS = [("es", "es"), ("is", "is"), ("so", "so"), ("ce", "ʃe"), ("dahoam", "dahoam")]


def test_third_real_sentence_recording(db_session, language):
    for form, ipa in DAHOAM_WORDS:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, DAHOAM_RECOGNISED)

    # "is so" said as "isso" still splits right: the words share the s.
    assert [t.ipa for t in result.tokens] == ["ɪs", "ɪs", "so", "ʃe", "davham"]
    assert [t.spelling for t in result.tokens[2:]] == ["so", "ce", "dahoam"]
    # The recogniser heard the same ɪs for "Es" and "is", halfway between e and
    # i, so both are offered; picking needs word-sequence knowledge (phase 3).
    for token in result.tokens[:2]:
        assert token.ambiguous
        assert {c.form for c in token.candidates} == {"es", "is"}


@pytest.mark.xfail(
    strict=True,
    reason="Needs word-sequence knowledge (phase 3): es/is sound the same here, "
    "'isso' can split as 'i so' once 'i' is a word, and the misheard 'dʌvham' "
    "fits 'da ham' better than 'dahoam'.",
)
def test_third_sentence_with_realistic_dictionary(db_session, language):
    for form, ipa in DAHOAM_WORDS + [("i", "i"), ("da", "da"), ("am", "am"), ("ham", "ham")]:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, DAHOAM_RECOGNISED)

    assert result.text == "Es is so ce dahoam"


def test_fourth_real_sentence_recording(db_session, language):
    # "di" is really said with a reduced ə, conventionally written i.
    for form, ipa in [("i", "i"), ("hób", "hɔb"), ("di", "də"), ("gean", "gean")]:
        _seed(db_session, language, form, ipa)

    recognised = "iː h ɔ p t ə ɡ ɛ n"
    result = transcription_service.transcribe_ipa(db_session, language.id, recognised)

    assert result.text == "I hób di gean"


def test_reduced_vowel_is_spelled_i():
    assert spell_segments(segments("də")) == "di"


DEANDL_RECOGNISED = "d ɪ s ɪ s a ʃ eː n s t ɛ n d ə l"  # "Des is a cens deandl"
DEANDL_WORDS = [("des", "des"), ("is", "is"), ("a", "a"), ("cens", "ʃens"), ("deandl", "deandl")]


def test_fifth_real_sentence_recording(db_session, language):
    for form, ipa in DEANDL_WORDS:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, DEANDL_RECOGNISED)

    assert result.text == "Des is a cens deandl"


def test_tie_goes_to_the_word_spelled_like_what_was_heard(db_session, language):
    # ɪs is equally close to "es" and "is"; the letter rules spell ɪs as "is".
    for form, ipa in DEANDL_WORDS + [("es", "es"), ("da", "da"), ("de", "de")]:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, DEANDL_RECOGNISED)

    assert result.text == "Des is a cens deandl"
    assert {c.form for c in result.tokens[1].candidates} == {"is", "es"}


VISDS_RECOGNISED = "ɪ s t ɛ s h aɪ t ts uː ʃ eː v ɪ s t ɛ s"  # "Is des haid so ce, visds's?"
VISDS_WORDS = [
    ("is", "is"),
    ("des", "des"),
    ("haid", "haid"),
    ("so", "so"),
    ("ce", "ʃe"),
    ("visds", "visds"),
    # visds + shortened es: two s sounds with a short e (or a pause) between.
    ("visds's", "visdsəs"),
    ("es", "es"),
    ("da", "da"),
    ("du", "du"),
    ("a", "a"),
]


def test_sixth_real_sentence_recording(db_session, language):
    for form, ipa in VISDS_WORDS:
        _seed(db_session, language, form, ipa)

    # The recogniser doubled the t where "haid so" runs together (haɪ t ts uː).
    result = transcription_service.transcribe_ipa(db_session, language.id, VISDS_RECOGNISED)

    assert [t.spelling for t in result.tokens[:5]] == ["Is", "des", "haid", "so", "ce"]


@pytest.mark.xfail(
    strict=True,
    reason="Recogniser heard only one of the two s sounds in visds's (vɪstɛs), so "
    "plain 'visds' fits better; needs a trained recogniser (phase 2).",
)
def test_sixth_sentence_keeps_the_final_es(db_session, language):
    for form, ipa in VISDS_WORDS:
        _seed(db_session, language, form, ipa)

    result = transcription_service.transcribe_ipa(db_session, language.id, VISDS_RECOGNISED)

    assert result.text in ("Is des haid so ce visds's", "Is des haid so ce visds es")


def test_decodes_mp4_with_index_at_the_end(tmp_path):
    # MP4/m4a (phone and Safari recordings) keeps its moov index after the
    # audio. Once the file outgrows ffmpeg's read buffer (~64 KB) it can't be
    # decoded from a pipe, which once surfaced as "The audio file is empty".
    import shutil
    import subprocess

    pytest.importorskip("numpy")
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    clip = tmp_path / "clip.m4a"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=duration=10", str(clip)],
        check=True,
    )
    assert clip.stat().st_size > 64 * 1024

    wave = phoneme_recognizer._decode_audio(clip.read_bytes())

    assert wave.size == pytest.approx(10 * phoneme_recognizer.SAMPLE_RATE, rel=0.05)
