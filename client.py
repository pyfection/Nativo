import json

from kivy.network.urlrequest import UrlRequest

from config import api_url


def on_error(req, result, callback):
    print("Failure:", req, result)
    callback(result)


def login(on_success, on_failure, username, password):
    def _on_success(req, token):
        on_success(token)

    url = f"{api_url}/token/"
    UrlRequest(
        url,
        method="POST",
        req_headers={
            'content-type': "multipart/form-data",
        },
        req_body={"username": username, "password": password},
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_multiples(keyword, on_success, on_failure, options=None):
    def _on_success(req, words):
        on_success(words)

    options = options or {}
    url = f"{api_url}/{keyword}/"
    UrlRequest(
        url,
        method="POST",
        req_body=json.dumps(options),
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_word(on_success, on_failure, id: int):
    def _on_success(req, word):
        on_success(word)

    url = f"{api_url}/word/?_id={id}"
    UrlRequest(
        url,
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_words(on_success, on_failure, options=None, limit=10):
    get_multiples("words", on_success, on_failure, options)


def upsert_word(on_success, on_failure, word: dict):
    def _on_success(req, word_):
        on_success(word_)

    url = f"{api_url}/word/"
    UrlRequest(
        url,
        method="PUT",
        req_body=json.dumps(word),
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))


def get_languages(on_success, on_failure, options=None):
    get_multiples("languages", on_success, on_failure, options)


def get_localization(on_success, on_failure, language):
    def _on_success(req, localization):
        on_success(localization)

    url = f"{api_url}/localization/?language={language}"
    UrlRequest(
        url,
        on_success=_on_success,
        on_failure=lambda req, result: on_error(req, result, on_failure),
        on_error=lambda req, result: on_error(req, result, on_failure))
