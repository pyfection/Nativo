
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from widgets.docedit import TextEdit

from db.db import db


Builder.load_file('views/docedit.kv')


class DocEditView(MDBoxLayout):
    uid = StringProperty('')
    doc = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def link_word(self):
        return self.toolbar.ids['right_actions'].children[0]

    def on_uid(self, _, uid):
        if uid:
            self.doc = db.get_doc(uid)
            text = self.doc['text']
        else:
            text = ''
        self.text_edit.open(text)

    def new_doc(self):
        self.uid = ''

    def save(self):
        text = self.text_edit.text
        self.doc['text'] = text
        db.upsert_doc(**self.doc)

    def open_link_word(self):
        self.word_edit.new_word()
        self.dialog_confirm_button.text = "LINK"
        self.word_edit.word.text = self.text_edit.active_widget.text
        self.word_edit_dialog.open()
