import os
from functools import partial
from kivy.properties import BooleanProperty, ObjectProperty 
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.gridlayout import GridLayout

from databaseitem import FaceObjectWidget

Builder.load_file('logface.kv')

class LogFaceObjectBox(BoxLayout):

    stackLayout = ObjectProperty(None)
    contentBox = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def add_item(self, id, str_datalist, face_texture):
        # pass empty list for img_datalist argument
        self.stackLayout.add_widget(FaceObjectWidget(id, str_datalist = str_datalist, face_texture = face_texture))


class LogFaceObjectStack (FocusBehavior, CompoundSelectionBehavior, GridLayout):

    selectedData = ObjectProperty(None)
    contentLayout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(selectedData = self.show_data_content)

    def show_data_content(self, *args):
        '''display data content in content layout'''
        if self.contentLayout:
            # below function returns: id, dataID, dataFirstName, dataLastName, dataImage
            # selectedData is object of type FaceObjectWidget
            id,_,_,_,_ = self.selectedData.get_data()
            self.contentLayout.display_detection_log(id)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super().keyboard_on_key_down(window, keycode, text, modifiers):
            return True
        if self.select_with_key_down(window, keycode, text, modifiers):
            return True
        return False

    def keyboard_on_key_up(self, window, keycode):
        if super().keyboard_on_key_up(window, keycode):
            return True
        if self.select_with_key_up(window, keycode):
            return True
        return False

    def add_widget(self, widget):
        super().add_widget(widget)
        widget.bind(on_touch_down = self.widget_touch_down, on_touch_up = self.widget_touch_up)
    
    def widget_touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.select_with_touch(widget, touch)
    
    def widget_touch_up(self, widget, touch):
        if self.collide_point(*touch.pos) and (not (widget.collide_point(*touch.pos) or self.touch_multiselect)):
            self.deselect_node(widget)
    
    def select_node(self, node):
        node.backgroundImage.source = 'images/databaseview/databaseitem_selected.png'
        self.selectedData = node
        return super().select_node(node)
        
    def deselect_node(self, node):
        super().deselect_node(node)
        node.backgroundImage.source = 'images/databaseview/databaseitem_normal.png'
    
    def clear_selection(self, widget=None):
        return super().clear_selection()

    def on_selected_nodes(self,grid,nodes):
        pass
