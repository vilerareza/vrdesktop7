import io
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior

Builder.load_file('databaseitem.kv')

class DatabaseItem(ButtonBehavior, FloatLayout):
    # TO EVALUATE TO DELETE THIS CLASS
    selected = BooleanProperty (False)
    id = ''
    dataID = ''
    dataFirstName = ''
    dataLastName = ''
    dataImage = ObjectProperty(None)
    backgroundImage = ObjectProperty(None)
    
    def __init__(self, data_list, **kwargs):
        super().__init__(**kwargs)
        self.id = data_list[0]
        self.dataID = data_list[1]
        self.dataFirstName = data_list[2]
        self.dataLastName = data_list[3]
        self.ids.data_id_label.text = self.dataID
        self.ids.data_firstname_label.text = self.dataFirstName
        self.ids.data_lastname_label.text = self.dataLastName 
        self.dataImage.source = data_list[4]

class FaceObjectWidget(ButtonBehavior, FloatLayout):
    '''Class to represent face object in a parent layout'''
    selected = BooleanProperty (False)
    id = ''
    dataID = StringProperty('')
    dataFirstName = StringProperty('')
    dataLastName = StringProperty('')
    dataImage = ObjectProperty(None)
    backgroundImage = ObjectProperty(None)
    
    def __init__(self, id, str_datalist = '', img_datalist=[], face_texture=None, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.dataID = str_datalist[0]
        self.dataFirstName = str_datalist[1]
        self.dataLastName = str_datalist[2]
        self.imgDataList = img_datalist
        self.dataImage.texture = face_texture
    
    def get_data(self):
        return [self.id, self.dataID, self.dataFirstName, self.dataLastName, self.dataImage]