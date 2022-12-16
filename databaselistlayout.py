from kivy.properties import BooleanProperty, ObjectProperty 
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.behaviors import FocusBehavior


class DatabaseListLayout (FocusBehavior, CompoundSelectionBehavior, StackLayout):

    databaseContentBox = ObjectProperty
    selectedData = ObjectProperty(None)
    isDataSelected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        widget.bind(on_touch_down = self.widget_touch_down)
    
    def widget_touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.select_with_touch(widget, touch)
    
    def select_node(self, node):
        node.backgroundImage.source = 'images/databaseview/databaseitem_selected.png'
        self.selectedData = node
        self.isDataSelected = True
        # Display the face info in the face content box
        if self.databaseContentBox:
            self.databaseContentBox.change_config(node)
        return super().select_node(node)
        
    def deselect_node(self, node):
        super().deselect_node(node)
        node.backgroundImage.source = 'images/databaseview/databaseitem_normal.png'
        # Check if nothing is selected
        if len(self.selected_nodes) == 0:
            self.isDataSelected = False
    
    def clear_selection(self, widget=None):
        return super().clear_selection()

    def on_selected_nodes(self,grid,nodes):
        pass