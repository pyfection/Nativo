import re

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.stacklayout import StackLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.label import Label

from widgets.word_edit import WordEdit
from sentence_lexer import SentenceLexer

Builder.load_file('widgets/docedit.kv')


class Raw(CodeInput):
    def __init__(self, **kwargs):
        super().__init__(lexer=SentenceLexer(), **kwargs)
        self.lexer.links_positions = []
        self.bind(text=self._process)
        self.bind(cursor=self.check_cursor)
        self.last_cursor = (0, 0)
        # ToDo: do same for del key as for backspace
        # ToDo: open side panel with word, if caret is to the right of it
        # ToDo: open side panel with selection with button to add it as a word
        # ToDo: add option for adding new word to extend selection (ignore leading and trailing whitespace and select remaining word characters

    def open(self, text):
        self.lexer.links_positions.clear()
        self.process(text)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print(window, keycode, text, modifiers)
        print(len(self.selection_text), self.selection_from)
        if keycode[1] == 'backspace':
            index = self.selection_from
            delete = max(1, len(self.selection_text))
            self._update_links_after(index, -delete)
            cursor = self.get_cursor_from_index(index-1)
            link_pos = self._cursor_in_link(cursor)
            if link_pos:
                i, start, end = link_pos
                self.lexer.links_positions.pop(i)
                self.select_text(start, end)
                self.delete_selection()
                return
        super().keyboard_on_key_down(window, keycode, text, modifiers)

    def insert_text(self, substring, from_undo=False):
        add = len(substring)
        self._update_links_after(self.cursor_index(), add)
        return super().insert_text(substring, from_undo=from_undo)

    def check_cursor(self, inst, cursor):
        link_pos = self._cursor_in_link()
        if link_pos:
            index = self.cursor_index()
            i, start, end = link_pos
            if index < self.cursor_index(self.last_cursor):
                # cursor moved to left
                self.cursor = self.get_cursor_from_index(start)
            elif index > self.cursor_index(self.last_cursor):
                # cursor moved right
                self.cursor = self.get_cursor_from_index(end)
        self.last_cursor = self.cursor

    def _cursor_in_link(self, cursor=None):
        cursor = cursor or self.cursor
        for i, (start, end) in enumerate(self.lexer.links_positions):
            index = self.cursor_index(cursor)
            if start < index < end:
                return i, start, end

    def _links_after(self, index):
        for i, (start, end) in enumerate(self.lexer.links_positions):
            if index < start:
                return i

    def _update_links_after(self, index, change):
        for i, (start, end) in enumerate(self.lexer.links_positions):
            if index < start:
                self.lexer.links_positions[i] = (start+change, end+change)

    def _process(self, inst, text):
        self.process(text)

    def process(self, raw_text):
        def assign_cursor(dt):
            self.cursor = new_cursor
        new_cursor = None
        text = ''
        i = 0
        j = 0
        while raw_text:
            match = re.search(r'\[\[[\w-]+(?::\w)?]]($)?', raw_text)
            if match:
                text += raw_text[:match.start()]
                i += match.start()
                j += match.start()
                linked = re.sub(r'[\[\]]', '', match.group())
                uid, *options = linked.split(':')
                app = App.get_running_app()
                word = app.db.get_word(uid)
                s = match.end() - match.start()
                if word is None:
                    # Matching, but can't be found, so just let it be
                    j += s
                    text += match.group()
                else:
                    l = len(word['word'])
                    self.lexer.links_positions.append((j, j+l))
                    j += l
                    text += word['word']
                    new_cursor = self.get_cursor_from_index(self.cursor_index() + (l - s) + 1)
                i += s
                raw_text = raw_text[match.end():]
            else:
                # No more links
                text += raw_text
                break

        self.unbind(text=self._process)
        self.text = text
        self.bind(text=self._process)
        if new_cursor is not None:
            Clock.schedule_once(assign_cursor)


class DocEdit(BoxLayout):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.content = FloatLayout()
        self.add_widget(self.content)
        self.raw = Raw()
        # self.raw.bind(text=self._on_change)
        # self.raw.bind(size=self._on_change)
        self.content.add_widget(self.raw)

        self.text_options = BoxLayout()
        self.word_options = BoxLayout()

    def on_text(self, _, text):
        self.raw.open(text)

    def _on_change(self, *args):
        return
        print("on change")
        children = [c for c in self.content.children if c is not self.raw]
        if children:
            self.content.clear_widgets(children)
        text = self.raw.text
        i = 0
        while text:
            match = re.search(r'\[\[[\w-]+(?::\w)?]]($)?', text)
            print('match', match, text)
            if match:
                i += match.start()
                self.raw.cursor = self.raw.get_cursor_from_index(i)
                linked = re.sub(r'[\[\]]', '', match.group())
                uid, *options = linked.split(':')
                app = App.get_running_app()
                word = app.db.get_word(uid)
                if word is None:
                    link = Link(
                        uid=uid,
                        text=match.group(),
                        x=self.raw.cursor_pos[0],
                        y=self.raw.cursor_pos[1]-24
                    )
                else:
                    link = Link(
                        uid=uid,
                        text=word['word'],
                        word_info=word,
                        x=self.raw.cursor_pos[0],
                        y=self.raw.cursor_pos[1]-24
                    )
                self.content.add_widget(link)
                i += match.end() - match.start()
                text = text[match.end():]
            else:
                # No more links
                break
