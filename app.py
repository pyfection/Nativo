
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager

import config
from db.db import db

Window.size = (480, 800)


Factory.register('Manager', module='app')
# Factory.register('AuthPage', module='pages.auth')
Factory.register('MainView', module='views.main')
Factory.register('DocListView', module='views.doclist')
Factory.register('DocEditView', module='views.docedit')
Factory.register('DocViewView', module='views.docview')
Factory.register('WordListView', module='views.wordlist')


class Manager(ScreenManager):

    def goto(self, screen_name, direction='left'):
        # Implemented because switch_to somehow removed the screen
        self.transition.direction = direction
        self.current = screen_name


class NativoApp(MDApp):
    title = 'Nativo'
    db = db
    authenticated = BooleanProperty(config.debug)

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Indigo"
        self.theme_cls.theme_style = "Dark"

    def edit_doc(self, uid=None):
        self.root.manager.current = 'docedit'
        if uid:
            self.root.docedit.uid = uid
        else:
            self.root.docedit.new_doc()

    def view_doc(self, uid):
        self.root.manager.current = 'docview'
        doc = self.db.get_doc_trans(uid)
        self.root.docview.uid = uid
        self.root.docview.title = doc['title']
        self.root.docview.text = doc['text']
        self.root.docview.lang = doc['lang']
        self.root.docview.creator = doc['creator']

    def edit_word(self, uid=None):
        self.root.manager.current = 'wordedit'
        if uid:
            self.root.wordedit.display_word(uid)
        else:
            self.root.wordedit.new_word()
