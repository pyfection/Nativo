
from kivy.app import App
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from db.db import db


Builder.load_file('widgets/word_edit.kv')


class WordEdit(MDBoxLayout):
    word_uid = None
    desc_uid = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang_choices = [{"text": db.lang_name_trans[lang['name']]} for lang in db.get_langs()]
        self.lang_selector = MDDropdownMenu(
            caller=self.lang,
            items=self.lang_choices,
            width_mult=4,
        )
        self.lang_selector.bind(on_release=self._update_language)

    def _update_language(self, instance_menu, instance_menu_item):
        self.lang.text = instance_menu_item.text
        self.lang_selector.dismiss()

    def new_word(self):
        self.word_uid = None
        self.desc_uid = None
        self.word.text = ''
        self.lang.text = ''
        self.desc.text = ''
        self.creator.text = App.get_running_app().db.user

    def display_word(self, uid):
        self.word_uid = uid
        word = db.get_word(uid)
        self.desc_uid = word['description']

        self.word.text = word['word']
        self.lang.text = db.lang_name_trans[db.get_lang(word['lang'])['name']]
        self.desc.text = db.get_document(self.desc_uid) if self.desc_uid else ''
        self.creator.text = word['creator']

    def show_word_suggestions(self):
        print('show word suggestions')

    def update(self):
        app = App.get_running_app()
        user = self.creater.text if self.creator.text else app.db.user
        desc_uid = None
        if self.description.text:
            desc_uid = app.db.upsert_document(self.desc_uid, self.description.text, self.lang.text, user)
        app.db.upsert_word(
            uid=self.word_uid, word=self.word.text, lang=self.lang.text, creator=user, description=desc_uid
        )
