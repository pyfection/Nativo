
from kivymd.app import App
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from widgets.word_edit import WordEdit
from widgets.docedit import WordInput, WordButton


Builder.load_file('pages/docedit.kv')


class DocEditPage(Screen):
    text = StringProperty('')

    def __init__(self, **kwargs):
        app = App.get_running_app()
        super().__init__(**kwargs)
        self.word_edit = WordEdit()
        self.word_edit.size_hint_y = None
        self.word_edit.height = sum(c.height for c in self.word_edit.children)
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
                MDFlatButton(
                    text="UPDATE", text_color=app.theme_cls.primary_color
                ),
            ],
        )

    @property
    def link_word(self):
        return self.toolbar.ids['right_actions'].children[0]

    def on_active_widget(self, widget):
        if isinstance(widget, WordInput):
            self.link_word.disabled = False
        elif isinstance(widget, WordButton) and widget.link:
            self.link_word.disabled = True
            self.word_edit.display_word(widget.link)
            self.word_edit_dialog.open()
        else:
            raise ValueError("Active widget has to be either WordInput or WordButton")

    def on_text(self, _, text):
        self.text_edit.open(text)
