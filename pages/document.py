
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.lang.builder import Builder


Builder.load_file('pages/doc.kv')


class DocEditPage(Screen):
    def prepare_edit(self, uid):
        self.document.text

    def update(self):
        print(self.document.text)
        return
        app = App.get_running_app()
        user = self.creater.text if self.creator.text else app.db.user
        desc_uid = None
        if self.description.text:
            desc_uid = app.db.upsert_document(self.desc_uid, self.description.text, self.lang.text, user)
        app.db.upsert_doc(
            uid=self.doc_uid, doc=self.doc.text, lang=self.lang.text, creator=user, description=desc_uid
        )
