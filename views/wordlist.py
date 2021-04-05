
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from db.db import db


Builder.load_file('views/wordlist.kv')


class WordLine(MDBoxLayout):
    uid = StringProperty()
    word = StringProperty()
    lang = StringProperty()
    creator = StringProperty()
    description = StringProperty()


class WordListView(MDBoxLayout):
    def on_kv_post(self, inst):
        words = db.get_words()
        for word in words:
            word.pop('phrases')
            word.pop('description')
            line = WordLine(**word)
            self.words.add_widget(line)
