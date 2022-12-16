from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_file('progressbox.kv')

class ProgressBox(BoxLayout):
    ProgressBar = ObjectProperty(None)
    ProgressLabel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass
