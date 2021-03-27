
from kivy.properties import StringProperty
from kivy.lang.builder import Builder
from kivymd.uix.boxlayout import MDBoxLayout


Builder.load_file('views/docview.kv')


class DocViewView(MDBoxLayout):
    title = StringProperty('')
    text = StringProperty('')
    lang = StringProperty('')
    creator = StringProperty('')
