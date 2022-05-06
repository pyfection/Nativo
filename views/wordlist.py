
from kivy.properties import StringProperty, NumericProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

import client


Builder.load_file('views/wordlist.kv')


class WordLine(MDBoxLayout):
    uid = StringProperty()
    word = StringProperty()
    lang = StringProperty()
    creator = StringProperty()
    description = StringProperty()


class WordList(MDBoxLayout):
    def load(self):
        client.get_words(on_success=self.display_words, on_failure=print)  # ToDo: proper fail handling

    def display_words(self, words):
        self.words.clear_widgets()
        for word in words:
            line = WordLine()
            line.uid = word["_id"]
            line.word = word["word"]
            line.lang = word["language"]
            line.creator = word["creator"]
            line.description = "Descriptions need to be added to words"  # word["description.text"]
            self.words.add_widget(line)
