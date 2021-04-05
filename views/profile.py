
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout

from db.db import db


Builder.load_file('views/profile.kv')


class ProfileView(MDBoxLayout):
    email = StringProperty()
    bio = StringProperty()

    def show_profile(self, email):
        self.email = email

    def on_email(self, email):
        user = db.get_user(email)
        self.bio = user.get('bio', '')
