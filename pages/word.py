
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang.builder import Builder


Builder.load_file('pages/word.kv')


class WordPage(Screen):
    word_uid = None
    desc_uid = None

    def display_word(self, word):
        app = App.get_running_app()
        self.word_uid = word['uid']
        self.desc_uid = word['description']

        self.word.text = word['word']
        self.lang.text = word['lang']
        self.description.text = app.db.get_document(self.desc_uid) if self.desc_uid else ''
        self.creator.text = word['creator']

    def prepare_create(self):
        self.word_uid = None
        self.desc_uid = None
        self.creator.text = App.get_running_app().db.user

    def update(self):
        app = App.get_running_app()
        user = self.creater.text if self.creator.text else app.db.user
        desc_uid = None
        if self.description.text:
            desc_uid = app.db.upsert_document(self.desc_uid, self.description.text, self.lang.text, user)
        app.db.upsert_word(
            uid=self.word_uid, word=self.word.text, lang=self.lang.text, creator=user, description=desc_uid
        )
