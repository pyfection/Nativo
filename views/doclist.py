
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from db.db import db


Builder.load_file('views/doclist.kv')


class DocLine(MDBoxLayout):
    uid = StringProperty()
    title = StringProperty()
    desc = StringProperty()


class DocListView(MDBoxLayout):
    def on_kv_post(self, inst):
        docs = db.get_docs_short()
        for doc in docs:
            line = DocLine(**doc)
            self.documents.add_widget(line)
