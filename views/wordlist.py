
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from models.word import Word

Builder.load_file('views/wordlist.kv')


class WordLine(MDBoxLayout):
    uid = StringProperty()
    word = StringProperty()
    lang = StringProperty()
    creator = StringProperty()
    description = StringProperty()


class WordList(MDBoxLayout):
    def load(self):
        words = Word.all()
        self.display_words(words)

    def display_words(self, words):
        self.words.clear_widgets()
        for word in words:
            line = WordLine()
            line.uid = word.id
            line.word = word.word
            # line.creator = word["creator"]
            line.description = word.description
            self.words.add_widget(line)
