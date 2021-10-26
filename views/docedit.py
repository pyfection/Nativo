
from kivy.properties import NumericProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from widgets.docedit import TextEdit

import client


Builder.load_file('views/docedit.kv')


class DocEditView(MDBoxLayout):
    uid = NumericProperty(None)
    doc = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def link_word(self):
        return self.toolbar.ids['right_actions'].children[0]

    def on_uid(self, _, uid):
        def set_document(document):
            self.doc = document
            self.creator_uid = document.creator.id
            self.text_edit.open(document.text)

        if uid:
            client.get_document(uid, on_success=set_document, on_failure=print)
        else:
            self.text_edit.open('')

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
