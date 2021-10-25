
from kivy.properties import StringProperty, NumericProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

import client


Builder.load_file('views/doclist.kv')


class DocLine(MDBoxLayout):
    uid = NumericProperty()
    title = StringProperty()
    description = StringProperty()


class DocListView(MDBoxLayout):
    def load(self):
        client.get_documents(on_success=self.display_documents, on_failure=print)

    def display_documents(self, documents):
        self.documents.clear_widgets()
        for document in documents:
            line = DocLine()
            line.uid = document.id
            line.title = document.title
            line.description = document.text
            self.documents.add_widget(line)
