import random
from kivy.properties import NumericProperty
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.uix.switch import Switch
from kivymd.uix.floatlayout import MDFloatLayout

class ColoredBox(BoxLayout):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(color[0],color[1],color[2])
            #Color(random.random(),random.random(),random.random())
            self.rect = Rectangle (pos=self.pos, size = self.size)
            self.bind (pos = self.update_rect, size = self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ColorFloatLayout(MDFloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(random.random(),random.random(),random.random())
            self.rect = Rectangle (pos=self.pos, size = self.size)
            self.bind (pos = self.update_rect, size = self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ColorLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_size = self.size
    def update_y_position(self, widget, y, offset):
        self.y = y - int(offset)
    def update_x_position(self, widget, x, offset):
        self.x = x + int (offset)
    def move_x(self, x):
        self.x = x
    def move_y(self, y):
        self.y = y
    

class TextInputBinded(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_size = self.size
    def update_y_position(self, widget, y, offset):
        self.y = y - int(offset)
    def update_x_position(self, widget, x, offset):
        self.x = x + int(offset)

class ToggleButtonBinded(ToggleButton): 
    def update_y_position(self, widget, y, offset):
        self.y = y - int(offset)
    def align_right(self, widget, right):
        self.right = right
    def update_x_position(self, widget, x, offset):
        self.x = x + int(offset)

class ButtonBinded(Button): 
    def update_y_position(self, widget, y, offset):
        self.y = y - int(offset)
    def update_x_position(self, widget, x, offset):
        self.x = x + int(offset)
    def align_right(self, widget, right):
        self.right = right
    def align_top(self, widget, top):
        self.top = top

class ImageButton (ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

class ImageToggle(ToggleButtonBehavior, Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

class LogoBar (FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SwitchBinded(Switch): 
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def update_y_position(self, widget, y, offset):
        self.y = y - int(offset)
    def update_x_position(self, widget, x, offset):
        self.x = x + int(offset)
    def align_right(self, widget, right):
        self.right = right
    def align_top(self, widget, top):
        self.top = top