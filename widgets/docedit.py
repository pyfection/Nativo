import re

from kivy.clock import Clock
from kivy.cache import Cache
from kivy.metrics import sp
from kivy.properties import StringProperty, BooleanProperty, ListProperty, BoundedNumericProperty, ObjectProperty
from kivy.lang.builder import Builder
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.textinput import TextInput
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.stacklayout import MDStackLayout
from kivymd.uix.textfield import MDTextFieldRect
from kivymd.uix.button import MDFlatButton, MDRaisedButton

from db.db import db
from widgets.word_edit import WordEdit

Cache_get = Cache.get
Cache_append = Cache.append
Builder.load_file('widgets/docedit.kv')

SPACE_CHARS = (' ', '.', ',', '!', '?')
COLOR_LINKED = (0, .5, 0, .2)
COLOR_UNLINKED = (0, 0, 1, .2)


class LineBreak(MDFlatButton):
    width = BoundedNumericProperty(
        1, min=1, max=None, errorhandler=lambda x: 1
    )


class WordButton(MDFlatButton):
    linked = StringProperty(None)
    highlight_color = ListProperty(COLOR_UNLINKED)

    def __init__(self, text_edit, **kwargs):
        self.text_edit = text_edit
        # self.text_color = COLOR_UNLINKED
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        FocusBehavior.ignored_touch.append(touch)
        return super().on_touch_down(touch)

    def on_press(self):
        if self.linked:
            self.text_edit.active_widget = self
            self.text_edit.word_input.focus = False
        else:
            # Replacing old word_input with new word_button
            self.text_edit.word_input.unfocus()

            # Replacing self with word_input
            index = self.text_edit.children.index(self)
            # self.text_edit.active_widget = self.text_edit.word_input
            self.text_edit.clear_widgets([self])
            self.text_edit.word_input.text = self.text
            self.text_edit.add_widget(self.text_edit.word_input, index=index)
            self.text_edit.word_input.focus = True

    def on_linked(self, instance, linked):
        if linked:
            # self.text_color = COLOR_LINKED
            self.highlight_color = COLOR_LINKED
        else:
            # self.text_color = COLOR_UNLINKED
            self.highlight_color = COLOR_UNLINKED


class WordInput(TextInput):
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
        self.text = ''
        return True


class TextEdit(MDStackLayout):
    active_widget = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.word_input = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for child in self.children:
                if child.collide_point(*touch.pos):
                    return super().on_touch_down(touch)
            self.word_input.unfocus()
            self.add_widget(self.word_input)
            FocusBehavior.ignored_touch.append(touch)
            self.word_input.focus = True

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
                if word is None:
                    # can't be found, let it be
                    word = last_word
                    linked = None
                else:
                    word = word['word']
                    linked = uid
                ph_len = len(match.group())
                if ph_len == len(last_word):
                    # button was already added
                    last_w.text = word
                    last_w.linked = linked
                else:
                    # split to add new button
                    last_w.text = last_w.text[:-ph_len]
                    last_w = WordButton(self, linked=linked, text=word)
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


class DocEdit(MDBoxLayout):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        self.text_edit = TextEdit()
        self.text_edit.bind(active_widget=self.on_active_widget)
        self.add_widget(self.text_edit)

        self.word_edit = WordEdit()
        self.link_word = MDRaisedButton(text="Link Word")

    def on_active_widget(self, inst, widget):
        children = self.children[1:]
        if children:
            self.clear_widgets(children)
        index = len(self.children)
        if isinstance(widget, WordInput):
            self.add_widget(self.link_word, index=index)
        elif isinstance(widget, WordButton):
            self.word_edit.display_word(widget.linked)
            self.add_widget(self.word_edit, index=index)
        else:
            raise ValueError("Active widget has to be either WordInput or WordButton")

    def on_text(self, _, text):
        self.text_edit.open(text)
