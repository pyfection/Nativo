import re

from kivymd.app import App
from kivy.cache import Cache
from kivy.metrics import sp
from kivy.properties import StringProperty, BooleanProperty, ListProperty, BoundedNumericProperty, ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.textinput import TextInput
from kivymd.theming import ThemableBehavior
from kivymd.uix.stacklayout import MDStackLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from widgets.word_edit import WordEdit
from db.db import db

Cache_get = Cache.get
Cache_append = Cache.append
Builder.load_file('widgets/docedit.kv')

SPACE_CHARS = (' ', '.', ',', '!', '?')
COLOR_LINKED = (0, .6, .1, 1)
COLOR_UNLINKED = (0, .42, .8, 1)
COLOR_BROKEN_LINK = (.66, .18, .1, 1)


class LineBreak(MDFlatButton):
    width = BoundedNumericProperty(
        1, min=1, max=None, errorhandler=lambda x: 1
    )


class WordButton(MDFlatButton):
    linked = BooleanProperty(None)
    link = StringProperty(None)
    highlight_color = ListProperty(COLOR_UNLINKED)

    def __init__(self, text_edit, **kwargs):
        self.text_edit = text_edit
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        FocusBehavior.ignored_touch.append(touch)
        return super().on_touch_down(touch)

    def on_press(self):
        if self.linked:
            self.text_edit.active_widget = None  # Setting to None first to trigger update
            self.text_edit.active_widget = self
            self.text_edit.word_input.focus = False

            self.text_edit.word_edit.display_word(self.link)
            self.text_edit.dialog_confirm_button.text = "UPDATE"
            self.text_edit.word_edit_dialog.open()
        elif self.text_edit.active_widget == self:  # Already active widget, but not linked
            # Replacing old word_input with new word_button
            self.text_edit.word_input.unfocus()

            # Replacing self with word_input
            index = self.text_edit.children.index(self)
            # self.text_edit.active_widget = self.text_edit.word_input
            self.text_edit.clear_widgets([self])
            self.text_edit.word_input.text = self.text
            self.text_edit.add_widget(self.text_edit.word_input, index=index)
            self.text_edit.word_input.focus = True
        else:  # First click, not linked
            self.text_edit.active_widget = self

            self.text_edit.word_edit.new_word(self.text)
            self.text_edit.dialog_confirm_button.text = "SAVE"
            self.text_edit.word_edit_dialog.open()

    def on_linked(self, instance, linked):
        self.check_color()

    def on_link(self, instance, link):
        self.linked = link is not None
        self.check_color()

    def check_color(self):
        if self.link:
            # self.text_color = COLOR_LINKED
            self.highlight_color = COLOR_LINKED
        elif self.linked and not self.link:
            self.highlight_color = COLOR_BROKEN_LINK
        else:
            # self.text_color = COLOR_UNLINKED
            self.highlight_color = COLOR_UNLINKED


class WordInput(ThemableBehavior, TextInput):
    def __init__(self, text_edit, **kwargs):
        self.text_edit = text_edit
        super().__init__(**kwargs)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print(keycode, text, modifiers)
        if keycode[1] == 'backspace' and self.cursor_index() == 0:
            # User wants to connect text input and the last widget
            index = self.text_edit.children.index(self)
            prev = self.text_edit.children[index+1]
            if isinstance(prev, LineBreak):
                prev.text = ''
            self.text_edit.clear_widgets([prev])
            self.text = prev.text + self.text
            self.cursor = self.get_cursor_from_index(len(prev.text))
            return
        elif keycode[1] == 'enter':
            index = self.text_edit.children.index(self)
            self.text_edit.add_widget(LineBreak(), index=index)
            self.unfocus()
            self.text_edit.add_widget(self, index=index)
            return

        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def insert_text(self, substring, from_undo=False):
        a = substring in SPACE_CHARS
        b = self.text and self.text[-1] in SPACE_CHARS
        if self.text and a ^ b:  # a XOR b, to separate space characters from word characters
            index = self.text_edit.children.index(self)
            self.unfocus()
            self.text = substring
            self.text_edit.add_widget(self, index=index)
        else:
            return super().insert_text(substring, from_undo=from_undo)

    def on_text(self, instance, text):
        self.width = self._lines_labels[0].width + sp(self.font_size)

    def on_focus(self, instance, focus):
        if focus:
            self.text_edit.active_widget = self
        else:
            self.unfocus()

    def unfocus(self):
        try:
            index = self.text_edit.children.index(self)
        except ValueError:
            return False
        self.text_edit.clear_widgets([self])
        if self.text:
            w = WordButton(self.text_edit, text=self.text)
            self.text_edit.add_widget(w, index=index)
            self.text_edit.active_widget = w
        self.text = ''
        return True


class TextEdit(MDStackLayout):
    active_widget = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = App.get_running_app()
        self.word_input = None
        self.open('')
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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for child in self.children:
                if child.collide_point(*touch.pos):
                    return super().on_touch_down(touch)
            self.word_input.unfocus()
            self.add_widget(self.word_input)
            FocusBehavior.ignored_touch.append(touch)
            self.word_input.focus = True
            self.active_widget = self.word_input

    def open(self, text):
        self.clear_widgets()

        last_c = ''
        last_w = None
        last_word = ''
        for c in text:
            # Trying to replace uid by actual word
            match = re.search(r'\[\[([\w-]+(?::\w)?)]]$', last_word)
            if match:
                uid = match.group(1)
                word = db.get_word(uid)
                linked = True
                if word is None:
                    # can't be found, let it be
                    word = last_word
                    link = None
                else:
                    word = word['word']
                    link = uid
                ph_len = len(match.group())
                if ph_len == len(last_word):
                    # button was already added
                    last_w.text = word
                    last_w.linked = linked
                    last_w.link = link
                else:
                    # split to add new button
                    last_w.text = last_w.text[:-ph_len]
                    last_w = WordButton(self, linked=linked, link=link, text=word)
                    self.add_widget(last_w)
                last_word = ''
                last_c = ''

            if c in SPACE_CHARS:
                # Add button to represent space
                last_word = ''
                if last_c in SPACE_CHARS:
                    last_w.text += c
                else:
                    last_w = WordButton(self, text=c)
                    self.add_widget(last_w)
                last_c = c

            else:
                # Add button to represent a word
                last_word += c
                if not last_c or last_c in SPACE_CHARS:
                    last_w = WordButton(self, text=c)
                    self.add_widget(last_w)
                else:
                    last_w.text += c
                last_c = c

        self.word_input = WordInput(self)
        self.add_widget(self.word_input)

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

    @property
    def text(self):
        text = ''

        for child in reversed(self.children):
            link = getattr(child, 'link', None)
            if link:
                text += f"[[{link}]]"
            else:
                text += child.text

        return text
