from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ObjectProperty
import threading

from manager import Manager

class VsDesktopApp(App):

    manager = ObjectProperty(None)
    stop_flag = BooleanProperty(False)
     
    def build (self):
        Window.minimum_width, Window.minimum_height = (500, 500)
        self.manager = Manager()
        return self.manager

    def on_stop(self):
        self.stop_flag = True
        print (threading.enumerate())
        self.manager.stop()

VsDesktopApp().run()

