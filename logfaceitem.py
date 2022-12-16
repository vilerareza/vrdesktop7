from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior

Builder.load_file('logfaceitem.kv')

class LogFaceItem(ButtonBehavior, FloatLayout):
    selected = BooleanProperty (False)
    dataImage = ObjectProperty(None)
    backgroundImage = ObjectProperty(None)
    
    def __init__(self, log_id, time_stamp, face_texture, frame_id, bbox,**kwargs):
        super().__init__(**kwargs)
        self.logID = log_id
        self.timeStamp = time_stamp
        self.frameID = frame_id
        self.bbox = bbox
        self.ids.date_label.text = self.timeStamp.strftime("%Y-%m-%d")
        self.ids.time_label.text = self.timeStamp.strftime("%H:%M:%S")
        self.dataImage.texture = face_texture