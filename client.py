from urllib.parse import urlencode
import json

from kivy.network.urlrequest import UrlRequest

from config import api_url
from db import SessionLocal, models, schemas


session = SessionLocal()


def on_error(req, result, callback):
    print("Failure:", req, result)
    callback(result)


def refresh_user(user: dict):
    user = schemas.User(**user)
    db_user = session.query(models.User).get(user.id)
    if db_user:
        db_user.email = user.email
        db_user.is_active = user.is_active
        db_user.about = user.about
    else:
        db_user = models.User(id=user.id, email=user.email, is_active=user.is_active, about=user.about)
        session.add(db_user)

    session.commit()
    return db_user


def refresh_language(language: dict):
    language = schemas.Language(**language)
    db_language = session.query(models.Language).get(language.id)
    if db_language:
        db_language.iso_639_3 = language.iso_639_3
    else:
        db_language = models.Language(id=language.id, iso_639_3=language.iso_639_3)

    for word in language.translations:
        word = refresh_word(word.dict())
        db_language.translations.append(word)
        session.add(db_language)
    session.commit()
    return db_language


def refresh_word(word: dict):
    word = schemas.Word(**word)
    db_word = session.query(models.Word).get(word.id)
    if db_word:
        db_word.word = word.word
        db_word.description.text = word.description.text
    else:
        language = refresh_language(word.language.dict())
        creator = refresh_user(word.creator.dict())
        description = refresh_document(word.description.dict())
        db_word = models.Word(id=word.id, word=word.word, language=language, creator=creator, description=description)
        session.add(db_word)
    session.commit()
    return db_word


def refresh_document(document: dict):
    document = schemas.Document(**document)
    db_document = session.query(models.Document).get(document.id)
    if db_document:
        db_document.title = document.title
        db_document.text = document.text
    else:
        language = refresh_language(document.language.dict())
        creator = refresh_user(document.creator.dict())
        db_document = models.Document(
            id=document.id, title=document.title, text=document.text, language=language, creator=creator
        )
        session.add(db_document)
    session.commit()
    return db_document


def get_word(id: int, on_success, on_failure):
    def _on_success(req, word):
        word = refresh_word(word)
        on_success(word)

    url = f"{api_url}/word/{id}"
    UrlRequest(
        url, on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_words(on_success, on_failure):
    def _on_success(req, words):
        words = [refresh_word(word) for word in words]
        on_success(words)

    url = f"{api_url}/words"
    UrlRequest(
        url, on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def upsert_word(word: dict, on_success, on_failure):
    def _on_success(req, word_):
        word_ = refresh_word(word_)
        on_success(word_)
    url = f"{api_url}/word"
    UrlRequest(
        url, method="PUT", req_body=json.dumps(word),
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_languages(on_success, on_failure):
    def _on_success(req, languages):
        languages = [refresh_language(language) for language in languages]
        on_success(languages)
    url = f"{api_url}/languages"
    UrlRequest(
        url, on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_documents(on_success, on_failure):
    def _on_success(req, documents):
        documents = [refresh_document(document) for document in documents]
        on_success(documents)
    url = f"{api_url}/documents"
    UrlRequest(
        url, on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))
