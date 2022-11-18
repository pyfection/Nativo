import json
from datetime import datetime

from kivy.app import App
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.properties import StringProperty

from models.word import Word

Builder.load_file("views/wordedit.kv")


class LangItem(OneLineAvatarIconListItem):
    pass


class WordEdit(MDBoxLayout):
    word_uid = StringProperty(None, allownone=True)
    creator_uid = StringProperty(None, allownone=True)

    def set_word(self, uid=None, word="", description=""):
        self.word_uid = uid
        self.word.text = word
        self.desc.text = description
        self.ids.confirm_button.text = "Create" if uid is None else "Update"

    def new_word(self, word=''):
        self.set_word(word=word)

    def display_word(self, uid):
        self.word_uid = uid
        word = Word.get(id=uid)
        self.set_word(word.id, word.word, word.description)
        self.creator_uid = word.creator

    def show_word_suggestions(self):
        print('show word suggestions')

    def jsonify_inputs(self):
        app = App.get_running_app()
        user_id = app.settings.get("user")["_id"]
        # last_coords = app.settings.get("user")["last_coords"]
        return {
            "id": self.word_uid,
            "word": self.word.text,
            "creator": user_id,
            "description": self.desc.text,
            # "foreign_descriptions": # ToDo: implement descriptions in other languages
            "stem_id": None,  # ToDo: implement selection of stem word
            # "tags": ["noun"]  # ToDo: implement proper part of speech selection
        }

    def draft(self):
        word = self.jsonify_inputs()
        name = str(datetime.now().timestamp())
        with open(f"drafts/{name}.json", "w") as f:
            json.dump(word, f)

    def save(self):
        data = self.jsonify_inputs()
        if not data["id"]:
            data.pop("id")
        word = Word(**data)
        word.commit()
        app = App.get_running_app()
        app.root.manager.go_back()
