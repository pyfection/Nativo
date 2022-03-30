import json
from datetime import datetime

from kivy.app import App
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.properties import NumericProperty, ObjectProperty, ListProperty

import client
from localization import localization as _

Builder.load_file('widgets/word_edit.kv')


class LangItem(OneLineAvatarIconListItem):
    pass


class WordEdit(MDBoxLayout):
    word_uid = NumericProperty(None, allownone=True)
    creator_uid = NumericProperty(None, allownone=True)

    def on_request_failure(self, result):
        print(result)

    def set_word(self, uid=None, word='', description=''):
        self.word_uid = uid
        self.word.text = word
        self.desc.text = description
        self.ids.confirm_button.text = "Create" if uid is None else "Update"

    def new_word(self, word=''):
        self.set_word(word=word)

    def display_word(self, uid):
        def set_word(word):
            self.set_word(word.id, word.word, word.description.text)
            self.creator_uid = word.creator.id
        self.word_uid = uid
        client.get_word(id=uid, on_success=set_word, on_failure=self.on_request_failure)

    def show_word_suggestions(self):
        print('show word suggestions')

    def jsonify_inputs(self):
        app = App.get_running_app()
        user_id = app.settings.get("user")["_id"]
        last_coords = app.settings.get("user")["last_coords"]
        return {
            "_id": self.word_uid,
            "word": self.word.text,
            "creator": user_id,
            "description": self.desc.text,
            "language":  app.settings.get("user")["language"],
            "locations": [
                {
                    "latitude": last_coords[0],
                    "longitude": last_coords[1],
                    "confirmer": user_id
                }
            ],
            "stem": None,  # ToDo: implement selection of stem word
            # "noun": ["singular"]  # ToDo: implement proper part of speech selection
        }

    def draft(self):
        word = self.jsonify_inputs()
        name = str(datetime.now().timestamp())
        with open(f"drafts/{name}.json", "w") as f:
            json.dump(word, f)

    def save(self):
        def on_success(result):
            app = App.get_running_app()
            app.root.manager.go_back()

        word = self.jsonify_inputs()

        client.upsert_word(
            word=word, on_success=on_success, on_failure=self.on_request_failure
        )
