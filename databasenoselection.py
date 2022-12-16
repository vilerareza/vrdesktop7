from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

Builder.load_file("databasenoselection.kv")

class DatabaseNoSelection (BoxLayout):
    text = StringProperty('')
