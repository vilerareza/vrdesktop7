from math import degrees
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

Builder.load_file('livegridlayout.kv')

class LiveGridLayout(GridLayout):
    nLive = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def show_initlabel(self):
        #self.add_widget(self.initLabel)
        self.add_widget(Label(text = '[color=cccccc]Select a Device to Start...[/color]', font_size = 17,
                        font_family = "arial", markup = True))

    def hide_initlabel(self):
        #self.remove_widget(self.initLabel)
        self.clear_widgets()