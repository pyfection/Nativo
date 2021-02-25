
from kivy.app import App
from kivy.factory import Factory
from kivy.properties import BooleanProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.actionbar import ActionGroup

import config
from db.db import DB


Factory.register('Manager', module='app')
Factory.register('AuthPage', module='pages.auth')
Factory.register('MainPage', module='pages.main')
Factory.register('WordPage', module='pages.word')
Factory.register('Menu', module='widgets.menu')
Factory.register('DocEdit', module='widgets.docedit')


class Manager(ScreenManager):

    def goto(self, screen_name, direction='left'):
        # Implemented because switch_to somehow removed the screen
        self.transition.direction = direction
        self.current = screen_name

    def create_word(self):
        if not App.get_running_app().db.token:
            raise ValueError("User not logged in!")
        word_screen = self.get_screen('word')
        word_screen.prefill()
        self.goto('word')

    def random_word(self):
        word = App.get_running_app().db.random_word()
        word_screen = self.get_screen('word')
        word_screen.view_word(word)
        self.goto('word')


class NativoApp(App):
    title = 'Nativo'
    db = DB()
    authenticated = BooleanProperty(config.debug)
    if config.debug:
        db.verify_user('me@mail.com', 'aoue')
