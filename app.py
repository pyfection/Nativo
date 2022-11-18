
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.storage.jsonstore import JsonStore

# They are just imported to register them as widget in KV files
from views.main import Main
from views.wordlist import WordList
from views.wordedit import WordEdit
import config

Window.size = (480, 800)


class Manager(ScreenManager):
    call_stack = ListProperty()

    def goto(self, screen_name, direction='left'):
        # Implemented because switch_to somehow removed the screen
        self.transition.direction = direction
        self.call_stack.append(self.current)
        self.current = screen_name

    def go_back(self, direction='right'):
        self.transition.direction = direction
        if self.call_stack:
            self.current = self.call_stack.pop()
        else:
            self.current = 'main'


class NativoApp(MDApp):
    title = "Nativo"
    authenticated = BooleanProperty(config.debug)
    settings = JsonStore("config.json")

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Indigo"
        self.theme_cls.theme_style = "Dark"

    # def edit_doc(self, uid=None):
    #     self.root.manager.current = 'docedit'
    #     if uid:
    #         self.root.docedit.uid = uid
    #     else:
    #         self.root.docedit.new_doc()
    #
    # def view_doc(self, uid):
    #     self.root.manager.current = 'docview'
    #     doc = self.db.get_doc_trans(uid)
    #     self.root.docview.uid = uid
    #     self.root.docview.title = doc['title']
    #     self.root.docview.text = doc['text']
    #     self.root.docview.lang = doc['lang']
    #     self.root.docview.creator = doc['creator']

    def edit_word(self, uid=None):
        self.root.manager.goto('wordedit')
        if uid:
            self.root.wordedit.display_word(uid)
        else:
            self.root.wordedit.new_word()
