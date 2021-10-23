
from kivy.properties import StringProperty, NumericProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

import client


Builder.load_file('views/wordlist.kv')


class WordLine(MDBoxLayout):
    uid = NumericProperty()
    word = StringProperty()
    lang = StringProperty()
    creator = StringProperty()
    description = StringProperty()


class WordListView(MDBoxLayout):
    def on_kv_post(self, inst):
        client.get_words(on_success=self.display_words, on_failure=print)

    def display_words(self, words):
        for word in words:
            line = WordLine()
            line.uid = word.id
            line.word = word.word
            line.lang = word.language.name()
            line.creator = word.creator.email
            line.description = word.description.text
            self.words.add_widget(line)
