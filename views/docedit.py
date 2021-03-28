
from kivymd.app import App
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from widgets.word_edit import WordEdit
from widgets.docedit import WordInput, WordButton

from db.db import db


Builder.load_file('views/docedit.kv')


class DocEditView(MDBoxLayout):
    uid = StringProperty('')
    doc = None

    def __init__(self, **kwargs):
        app = App.get_running_app()
        super().__init__(**kwargs)
        self.word_edit = WordEdit()
        self.word_edit.size_hint_y = None
        self.word_edit.height = sum(c.height for c in self.word_edit.children)
        self.dialog_confirm_button = MDFlatButton(
            text="UPDATE", text_color=app.theme_cls.primary_color,
            on_release=lambda *args: self.process_word()
        )
        self.word_edit_dialog = MDDialog(
            md_bg_color=(1, 1, 1, 1),  # app.theme_cls.bg_dark,  # For some reason keeps light color
            title="Edit Word",
            type="custom",
            content_cls=self.word_edit,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color,
                    on_release=lambda *args: self.word_edit_dialog.dismiss()
                ),
                self.dialog_confirm_button,
            ],
        )

    @property
    def link_word(self):
        return self.toolbar.ids['right_actions'].children[0]

    def on_active_widget(self, widget):
        if isinstance(widget, WordInput):
            self.link_word.disabled = False
        elif isinstance(widget, WordButton):
            self.link_word.disabled = True
            if widget.link:
                self.word_edit.display_word(widget.link)
                self.dialog_confirm_button.text = "UPDATE"
                self.word_edit_dialog.open()
            else:
                pass  # Unlinked word that lost focus
        else:
            raise ValueError("Active widget has to be either WordInput or WordButton")

    def on_uid(self, _, uid):
        if uid:
            self.doc = db.get_doc(uid)
            text = self.doc['text']
        else:
            text = ''
        self.text_edit.open(text)

    def save(self):
        text = self.text_edit.text
        self.doc['text'] = text
        db.upsert_doc(**self.doc)

    def open_link_word(self):
        self.word_edit.new_word()
        self.dialog_confirm_button.text = "LINK"
        self.word_edit.word.text = self.text_edit.active_widget.text
        self.word_edit_dialog.open()

    def process_word(self):
        uid = self.word_edit.word_uid
        desc_uid = self.word_edit.desc_uid
        word = self.word_edit.word.text
        desc_uid = db.upsert_doc(
            uid=desc_uid,
            title=f"Description of [{word}]",
            text=self.word_edit.desc.text,
            lang=self.word_edit.lang.lang_uid,
            creator=self.word_edit.creator.text,
        )

        uid = db.upsert_word(
            uid=uid,
            word=word,
            lang=self.word_edit.lang.lang_uid,
            creator=self.word_edit.creator.text,
            description=desc_uid,
        )

        self.text_edit.active_widget.text = word
        self.text_edit.active_widget.link = uid
        self.word_edit_dialog.dismiss()

        self.save()
