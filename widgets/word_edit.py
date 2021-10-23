
from kivy.app import App
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.properties import NumericProperty, ObjectProperty, ListProperty

import client


Builder.load_file('widgets/word_edit.kv')


class LangItem(OneLineAvatarIconListItem):
    uid = NumericProperty()


class WordEdit(MDBoxLayout):
    word_uid = NumericProperty(None, allownone=True)
    language_uid = NumericProperty(None, allownone=True)
    creator_uid = NumericProperty(None, allownone=True)
    lang_selector = ObjectProperty()
    lang_choices = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang_selector = MDDropdownMenu(
            caller=self.lang,
            items=self.lang_choices,
            width_mult=4,
        )
        self.lang_selector.bind(on_release=self._update_language)

    def on_request_failure(self, result):
        print(result)

    def _update_language(self, instance_menu, instance_menu_item):
        print('update language')
        self.lang.text = instance_menu_item.text
        self.lang.lang_uid = instance_menu_item.data['uid']
        self.lang_selector.dismiss()

    def set_lang_choices(self, languages):
        self.lang_choices = [
            {
                "text": lang.name() or '',
                "viewclass": "LangItem",
                "uid": lang.id
            }
            for lang in languages
        ]

    def set_word(self, uid=None, word='', language='', description=''):
        client.get_languages(self.set_lang_choices, print)
        self.word_uid = uid
        self.word.text = word
        self.lang.text = language
        self.desc.text = description

    def new_word(self, word=''):
        self.set_word(word=word)

    def display_word(self, uid):
        def set_word(word):
            self.set_word(word.id, word.word, word.language.name(), word.description.text)
            self.language_uid = word.language.id
            self.creator_uid = word.creator.id
        self.word_uid = uid
        client.get_word(uid, on_success=set_word, on_failure=self.on_request_failure)

    def show_word_suggestions(self):
        print('show word suggestions')

    def update(self):
        def on_success(result):
            print('update success', result)

        word = {
            'id': self.word_uid,
            'word': self.word.text,
            # ToDo: check what happens if language or creator not set
            'language_id': self.language_uid,
            'creator_id': self.creator_uid,
            'description': self.desc.text,
        }
        client.upsert_word(
            word=word, on_success=on_success, on_failure=self.on_request_failure
        )
