import random
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from mylayoutwidgets import ColorLabel

Builder.load_file("deviceitem.kv")

class DeviceItem(FloatLayout):
    deviceID = NumericProperty(0)
    deviceName = StringProperty("")
    hostName = ''
    wifiName = ''
    wifiPass = ''
    image = ObjectProperty(None)
    label = ObjectProperty(None)
    color = ObjectProperty((0,0,0))
    visionAI = BooleanProperty(False)
    imagePath = "images/not_device_selected5.png"

    def __init__(self, deviceID, deviceName, host_name, wifi_name, wifi_pass, deviceVisionAI, **kwargs):
        super().__init__(**kwargs)
        #self.orientation = 'vertical'
        self.padding = [10]
        self.spacing = 10
        self.deviceID = deviceID
        self.deviceName = deviceName
        self.hostName = host_name
        self.wifiName = wifi_name
        self.wifiPass = wifi_pass
        self.deviceVisionAI = deviceVisionAI
        #self.image = Image (source=imagePath, mipmap = True, size_hint = (1,1), pos_hint = {'center_x':0.5, 'center_y':0.5})
        #self.label = ColorLabel(text="[color=dddddd]"+deviceName+"[/color]", font_size = 16, font_family = "arial", halign = "center", valign = "top", size_hint = (None, None), size = (80,25), pos_hint = {'center_x':0.5, 'top': 1}, markup = True)
        #self.deviceLabel = Label(text = "", font_size = 18, font_family = "arial", halign = 'center', valign = 'middle', size_hint = (None, None), size = (120,40), pos_hint = {'center_x':0.5, 'center_y': 0.5}
        #self.add_widget (self.image)
        #self.add_widget (self.label)
